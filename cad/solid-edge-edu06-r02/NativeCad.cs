using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Collections.Generic;
using System.Web.Script.Serialization;
using System.Globalization;
using SE=SolidEdge.Part.Interop;
public static class NativeCad {
 public class Shape { public string type; public double x,y,r; public double[][] points; }
 public class Op { public double z,depth; public Shape[] shapes; public string label,kind; public int plane; }
 public class Part { public string name,notes,category; public Op[] ops; }
 public class Placement { public string part,label; public double[] position,rotation,matrix; }
 public class Design { public Part[] parts; public Placement[] placements; }
 public static void Build(string root) {
  var app=(SolidEdge.Framework.Interop.Application)Marshal.GetActiveObject("SolidEdge.Application");
  var data=new JavaScriptSerializer().Deserialize<Design>(File.ReadAllText(Path.Combine(root,"design.json")));
  Directory.CreateDirectory(Path.Combine(root,"parts"));Directory.CreateDirectory(Path.Combine(root,"stl_mm"));Directory.CreateDirectory(Path.Combine(root,"step"));
  var report=File.Exists(Path.Combine(root,"cad-verification.json"))?new JavaScriptSerializer().Deserialize<List<object>>(File.ReadAllText(Path.Combine(root,"cad-verification.json"))):new List<object>();
  foreach(var part in data.parts) {
   string path=Path.Combine(root,"parts",part.name+".par");
   if(File.Exists(path)&&File.Exists(Path.Combine(root,"step",part.name+".stp"))&&File.Exists(Path.Combine(root,"stl_mm",part.name+".stl"))) {Console.WriteLine("EXISTS "+part.name);continue;}
   bool exists=File.Exists(path);
   var doc=exists?(SE.PartDocument)app.Documents.Open(path):(SE.PartDocument)app.Documents.Add("SolidEdge.PartDocument",@"C:\Program Files\Siemens\Solid Edge 2021\Template\ISO Metric\iso metric part.par");
   doc.ModelingMode=SE.ModelingModeConstants.seModelingModeOrdered;
   SE.Model model=exists?doc.Models.Item(1):null;
   if(!exists)foreach(var op in part.ops) {
    var plane=doc.RefPlanes.Item(op.plane==0?1:op.plane);
    if(op.z!=0) plane=doc.RefPlanes.AddParallelByDistance(plane,Math.Abs(op.z)/1000,(SE.ReferenceElementConstants)(op.z>0?2:1));
    var p=doc.ProfileSets.Add().Profiles.Add(plane);
    foreach(var s in op.shapes) {
     if(s.type=="circle")p.Circles2d.AddByCenterRadius(s.x/1000,s.y/1000,s.r/1000);
     else {
      var lines=new List<SolidEdge.FrameworkSupport.Interop.Line2d>();
      for(int i=0;i<s.points.Length;i++){var a=s.points[i];var b=s.points[(i+1)%s.points.Length];lines.Add(p.Lines2d.AddBy2Points(a[0]/1000,a[1]/1000,b[0]/1000,b[1]/1000));}
      for(int i=0;i<lines.Count;i++)((SolidEdge.FrameworkSupport.Interop.Relations2d)p.Relations2d).AddKeypoint(lines[i],1,lines[(i+1)%lines.Count],0,true);
     }
    }
    int status=p.End((SE.ProfileValidationType)8193);
    if(status!=0)throw new Exception(part.name+" z="+op.z+" profile validation "+status+" shapes="+op.shapes.Length);
    Array profiles=new object[]{p};
    if(model==null) model=doc.Models.AddFiniteExtrudedProtrusion(1,ref profiles,SE.FeaturePropertyConstants.igRight,op.depth/1000);
    else if(op.kind=="cut") model.ExtrudedCutouts.AddFiniteMulti(1,ref profiles,SE.FeaturePropertyConstants.igRight,op.depth/1000);
    else model.ExtrudedProtrusions.AddFiniteMulti(1,ref profiles,SE.FeaturePropertyConstants.igRight,op.depth/1000);
    p.Visible=false;
   }
   var body=(SolidEdge.Geometry.Interop.Body)model.Body;
   if(body==null)throw new Exception(part.name+" has no final body after "+part.ops.Length+" operations");
   if(!exists){var style=((SolidEdge.Framework.Interop.FaceStyles)doc.FaceStyles).Add("EDU06 R02","");
   if(part.category.Contains("reference"))style.SetDiffuse(.25f,.29f,.32f);
   else if(part.name.Contains("gear")||part.name.Contains("pinion")||part.name.Contains("rack"))style.SetDiffuse(.68f,.82f,.60f);
   else style.SetDiffuse(.10f,.35f,.28f);
   body.Style=style;
   doc.SaveAs(path);}
   body=(SolidEdge.Geometry.Interop.Body)model.Body;
   Array lo=new double[3],hi=new double[3];body.GetRange(ref lo,ref hi);
   int count=0;Array pts=new double[0];object norms=null,uv=null,styles=null,faces=null;
   body.GetFacetData(.00002,out count,ref pts,out norms,out uv,out styles,out faces,false);
   double[] flat=new double[pts.Length];int idx=0;foreach(var v in pts)flat[idx++]=Convert.ToDouble(v)*1000;
   if(flat.Length!=count*9)throw new Exception("Unexpected facet layout "+flat.Length+" "+count);
   using(var w=new BinaryWriter(File.Create(Path.Combine(root,"stl_mm",part.name+".stl")))) {
    var header=new byte[80];System.Text.Encoding.ASCII.GetBytes("EDU06 Solid Edge facets; units mm; chord tolerance 0.02 mm").CopyTo(header,0);w.Write(header);w.Write((uint)count);
    for(int i=0;i<count;i++){int k=i*9;double ux=flat[k+3]-flat[k],uy=flat[k+4]-flat[k+1],uz=flat[k+5]-flat[k+2],vx=flat[k+6]-flat[k],vy=flat[k+7]-flat[k+1],vz=flat[k+8]-flat[k+2];double nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;double n=Math.Sqrt(nx*nx+ny*ny+nz*nz);w.Write((float)(nx/n));w.Write((float)(ny/n));w.Write((float)(nz/n));for(int j=0;j<9;j++)w.Write((float)flat[k+j]);w.Write((ushort)0);}
   }
   report.Add(new {name=part.name,volume_mm3=body.Volume*1e9,bounds_min_m=lo,bounds_max_m=hi,facets=count,category=part.category});
   File.WriteAllText(Path.Combine(root,"cad-verification.json"),new JavaScriptSerializer().Serialize(report));
   doc.SaveAs(Path.Combine(root,"step",part.name+".stp"));
   doc.Close(false);
   Console.WriteLine("BUILT "+part.name+" | facets "+count);
  }
  string ap=Path.Combine(root,"EDU06_R02_ASSEMBLY.asm");bool ae=File.Exists(ap);
  var asm=ae?(SolidEdge.Assembly.Interop.AssemblyDocument)app.Documents.Open(ap):(SolidEdge.Assembly.Interop.AssemblyDocument)app.Documents.Add("SolidEdge.AssemblyDocument",@"C:\Program Files\Siemens\Solid Edge 2021\Template\ISO Metric\iso metric assembly.asm");
  int oi=0;foreach(var item in data.placements){oi++;string pp=Path.Combine(root,"parts",item.part+".par");var occ=oi<=asm.Occurrences.Count?asm.Occurrences.Item(oi):asm.Occurrences.AddByFilename(pp);occ.Replace(pp,false);Array mat=item.matrix;occ.PutMatrix(ref mat,true);occ.Name=item.label;}
  if(ae)asm.Save();else asm.SaveAs(ap);
  ((SolidEdge.Framework.Interop.Window)app.ActiveWindow).View.Fit();
  asm.SaveAs(Path.Combine(root,"EDU06_R02_ASSEMBLY.stp"));
  Console.WriteLine("ASSEMBLY SAVED");
 }
 public static void Probe(string root) {
  var app=(SolidEdge.Framework.Interop.Application)Marshal.GetActiveObject("SolidEdge.Application");
  var doc=(SE.PartDocument)app.Documents.Add("SolidEdge.PartDocument",@"C:\Program Files\Siemens\Solid Edge 2021\Template\ISO Metric\iso metric part.par");
  doc.ModelingMode=SE.ModelingModeConstants.seModelingModeOrdered;
  var p=doc.ProfileSets.Add().Profiles.Add(doc.RefPlanes.Item(1));
  p.Circles2d.AddByCenterRadius(0,0,.018);
  p.Circles2d.AddByCenterRadius(0,0,.005);
  for(int i=0;i<4;i++){double t=i*Math.PI/2; p.Circles2d.AddByCenterRadius(.008*Math.Cos(t),.008*Math.Sin(t),.00115);}
  Console.WriteLine("profile status "+p.End((SE.ProfileValidationType)8193));
  Array profiles=new object[]{p};
  var m=doc.Models.AddFiniteExtrudedProtrusion(1,ref profiles,SE.FeaturePropertyConstants.igRight,.004);
  p.Visible=false;
  doc.SaveAs(Path.Combine(root,"AX_horn_adapter_ordered.par"));
  ((SolidEdge.Framework.Interop.Window)app.ActiveWindow).View.Fit();
  Array lo=new double[3],hi=new double[3];
  ((SolidEdge.Geometry.Interop.Body)m.Body).GetRange(ref lo,ref hi);
  Console.WriteLine("range: "+string.Join(",",(double[])lo)+" / "+string.Join(",",(double[])hi));
  doc.SaveAs(Path.Combine(root,"AX_horn_adapter_ordered.stp"));
 }
}
