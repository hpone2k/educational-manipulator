using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Collections.Generic;
using System.Web.Script.Serialization;
using System.Globalization;
using SE=SolidEdge.Part.Interop;
public static class NativeCad {
 public class Shape { public string type; public double x,y,r; public double[][] points; }
 public class Op { public double z,depth; public Shape[] shapes; public string label; }
 public class Part { public string name,notes,category; public Op[] ops; }
 public class Placement { public string part,label; public double[] position,rotation; }
 public class Design { public Part[] parts; public Placement[] placements; }
 public static void Build(string root) {
  var app=(SolidEdge.Framework.Interop.Application)Marshal.GetActiveObject("SolidEdge.Application");
  var data=new JavaScriptSerializer().Deserialize<Design>(File.ReadAllText(Path.Combine(root,"design.json")));
  Directory.CreateDirectory(Path.Combine(root,"parts"));Directory.CreateDirectory(Path.Combine(root,"stl_mm"));Directory.CreateDirectory(Path.Combine(root,"step"));
  var report=new List<object>();
  foreach(var part in data.parts) {
   string path=Path.Combine(root,"parts",part.name+".par");
   if(File.Exists(path)) {Console.WriteLine("EXISTS "+part.name);continue;}
   var doc=(SE.PartDocument)app.Documents.Add("SolidEdge.PartDocument",@"C:\Program Files\Siemens\Solid Edge 2021\Template\ISO Metric\iso metric part.par");
   doc.ModelingMode=SE.ModelingModeConstants.seModelingModeOrdered;
   SE.Model model=null;
   foreach(var op in part.ops) {
    var plane=doc.RefPlanes.Item(1);
    if(op.z!=0) plane=doc.RefPlanes.AddParallelByDistance(plane,op.z/1000,(SE.ReferenceElementConstants)2);
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
    else model.ExtrudedProtrusions.AddFiniteMulti(1,ref profiles,SE.FeaturePropertyConstants.igRight,op.depth/1000);
    p.Visible=false;
   }
   doc.SaveAs(path);
   var body=(SolidEdge.Geometry.Interop.Body)model.Body;
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
  var asm=(SolidEdge.Assembly.Interop.AssemblyDocument)app.Documents.Add("SolidEdge.AssemblyDocument",@"C:\Program Files\Siemens\Solid Edge 2021\Template\ISO Metric\iso metric assembly.asm");
  foreach(var item in data.placements){var occ=asm.Occurrences.AddByFilename(Path.Combine(root,"parts",item.part+".par"));occ.PutTransform(item.position[0]/1000,item.position[1]/1000,item.position[2]/1000,item.rotation[0]*Math.PI/180,item.rotation[1]*Math.PI/180,item.rotation[2]*Math.PI/180);}
  asm.SaveAs(Path.Combine(root,"EDU06_R01_LAYOUT_PROTOTYPE.asm"));
  ((SolidEdge.Framework.Interop.Window)app.ActiveWindow).View.Fit();
  asm.SaveAs(Path.Combine(root,"EDU06_R01_LAYOUT_PROTOTYPE.stp"));
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
