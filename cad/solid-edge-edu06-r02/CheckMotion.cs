using System;using System.IO;using System.Collections.Generic;using System.Web.Script.Serialization;using System.Runtime.InteropServices;
using A=SolidEdge.Assembly.Interop;using F=SolidEdge.Framework.Interop;
public static class CheckMotion {
 public class Place {public string label,part,node;public double[] matrix;}
 public class Pose {public string name; public Dictionary<string,double> q;public Place[] placements;}
 public class Data {public Place[] placements;public Pose[] poses;}
 public static void Run(string root,bool all) {
  var app=(F.Application)Marshal.GetActiveObject("SolidEdge.Application");
  var asm=(A.AssemblyDocument)app.Documents.Open(Path.Combine(root,"EDU06_R02_ASSEMBLY.asm"));
  var json=new JavaScriptSerializer();json.MaxJsonLength=20000000;
  var data=json.Deserialize<Data>(File.ReadAllText(Path.Combine(root,"design.json")));
  var occ=new List<A.Occurrence>();for(int i=1;i<=asm.Occurrences.Count;i++)occ.Add(asm.Occurrences.Item(i));
  if(occ.Count!=data.placements.Length)throw new Exception("Occurrence count mismatch");
  var reports=new List<object>();Directory.CreateDirectory(Path.Combine(root,"motion-checks"));
  foreach(var pose in data.poses) {
   if(!all&&pose.name!="home")continue;
   for(int i=0;i<occ.Count;i++){Array m=pose.placements[i].matrix;occ[i].PutMatrix(ref m,true);}
   asm.UpdateAll();
   Array set=occ.ConvertAll<object>(x=>x).ToArray();A.InterferenceStatusConstants status;
   object n,s1=null,s2=null,confirmed=null,interference;
   asm.CheckInterference(occ.Count,ref set,out status,4,Type.Missing,Type.Missing,false,Path.Combine(root,"motion-checks",pose.name+".txt"),15,out n,ref s1,ref s2,ref confirmed,out interference,true);
   var pairs=new List<object>();int count=Convert.ToInt32(n);
   if(count>0){var a=(Array)s1;var b=(Array)s2;var c=(Array)confirmed;for(int i=0;i<count;i++)pairs.Add(new {a=((A.Occurrence)a.GetValue(i)).Name,b=((A.Occurrence)b.GetValue(i)).Name,confirmed=c.GetValue(i)});}
   if(count==0&&status!=A.InterferenceStatusConstants.seInterferenceStatusNoInterference){
    string txt=File.ReadAllText(Path.Combine(root,"motion-checks",pose.name+".txt"));
    foreach(System.Text.RegularExpressions.Match match in System.Text.RegularExpressions.Regex.Matches(txt,@"(?m)^\s+\d+ of \d+\r?\n\s+([^\r\n]+)\r?\n\s+([^\r\n]+)"))pairs.Add(new {a=match.Groups[1].Value.Trim(),b=match.Groups[2].Value.Trim(),confirmed=true});count=pairs.Count;
   }
   reports.Add(new {pose=pose.name,q=pose.q,status=status.ToString(),interference_count=count,pairs=pairs});
   File.WriteAllText(Path.Combine(root,"motion-checks","results.json"),json.Serialize(reports));
   Console.WriteLine(pose.name+" | "+status+" | pairs "+count);
   var view=((F.Window)app.ActiveWindow).View;view.Fit();view.SaveAsImage(Path.Combine(root,"motion-checks",pose.name+".jpg"),1400,1000);
  }
  for(int i=0;i<occ.Count;i++){Array m=data.placements[i].matrix;occ[i].PutMatrix(ref m,true);}
  asm.Save();((F.Window)app.ActiveWindow).View.Fit();
 }
}
