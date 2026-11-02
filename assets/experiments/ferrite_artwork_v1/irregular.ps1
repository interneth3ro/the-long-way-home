param([switch]$Check)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
# Offline proof: painted material + oriented perimeter strips, not clipped deposits.
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.IO;
using System.Drawing;
using System.Drawing.Imaging;
using System.Drawing.Drawing2D;
using System.Runtime.InteropServices;
using System.Collections.Generic;

public static class FerriteIrregularProof {
    const int Cell=128, Pad=64, Radius=24, Band=112, Overlap=96;
    static string Root;
    static bool Check;
    static int Saved;
    static Tex Interior, North, South, West, East;
    static readonly string[] IDs={"l_shape","stepped","organic"};
    struct V {
        public double X,Y;
        public V(double x,double y){X=x;Y=y;}
        public static V operator +(V a,V b){return new V(a.X+b.X,a.Y+b.Y);}
        public static V operator -(V a,V b){return new V(a.X-b.X,a.Y-b.Y);}
        public static V operator *(V a,double k){return new V(a.X*k,a.Y*k);}
        public double Length {get{return Math.Sqrt(X*X+Y*Y);}}
        public V Unit {get{return this*(1/Length);}}
    }
    class Tex {
        public int W,H; public int[] Pixels;public int[] Rim;
        public Tex(Bitmap b) {
            W=b.Width;H=b.Height; Pixels=new int[W*H];
            var data=b.LockBits(new Rectangle(0,0,W,H),ImageLockMode.ReadOnly,PixelFormat.Format32bppArgb);
            try {for(int y=0;y<H;y++) Marshal.Copy(IntPtr.Add(data.Scan0,y*data.Stride),Pixels,y*W,W);}
            finally {b.UnlockBits(data);}
        }
        public Color At(int x,int y){return Color.FromArgb(Pixels[Math.Max(0,Math.Min(H-1,y))*W+Math.Max(0,Math.Min(W-1,x))]);}
        public void PrepareRim(bool horizontal,bool reverse) {
            Rim=new int[horizontal?W:H];int depth=horizontal?H:W;
            for(int t=0;t<Rim.Length;t++) {
                bool found=false;
                for(int j=0;j<depth;j++) {
                    int d=reverse?depth-1-j:j;
                    if((horizontal?At(t,d):At(d,t)).A>=240){Rim[t]=d;found=true;break;}
                }
                if(!found)throw new Exception("Missing painted edge at strip position "+t);
            }
        }
    }
    class Outline {
        public List<V> Curve=new List<V>();
        public List<V> Corners=new List<V>();
        public List<bool> Concave=new List<bool>();
        public int ConvexCount,ConcaveCount;
    }
    static Bitmap New(int w,int h){return new Bitmap(w,h,PixelFormat.Format32bppArgb);}
    static Tex Load(string name) {
        using(var b=new Bitmap(Path.Combine(Root,"components/"+name+".png"))) return new Tex(b);
    }
    static bool Occupied(string[] mask,int x,int y) {
        return y>=0&&y<mask.Length&&x>=0&&x<mask[0].Length&&mask[y][x]=='#';
    }
    static void ValidateMask(string[] m) {
        if(m.Length==0||m[0].Length==0) throw new Exception("Empty mask");
        int count=0;Point first=Point.Empty;
        for(int y=0;y<m.Length;y++) {
            if(m[y].Length!=m[0].Length) throw new Exception("Unequal mask rows");
            for(int x=0;x<m[0].Length;x++) {
                if(m[y][x]!='#'&&m[y][x]!='.') throw new Exception("Unknown occupancy token");
                if(m[y][x]=='#'){first=new Point(x,y);count++;}
            }
        }
        if(count==0) throw new Exception("No occupied cells");
        var visited=new HashSet<Point>();var q=new Queue<Point>();q.Enqueue(first);visited.Add(first);
        int[] dx={1,-1,0,0},dy={0,0,1,-1};
        while(q.Count>0){var p=q.Dequeue();for(int i=0;i<4;i++) {
            var n=new Point(p.X+dx[i],p.Y+dy[i]);
            if(Occupied(m,n.X,n.Y)&&visited.Add(n)) q.Enqueue(n);
        }}
        if(visited.Count!=count) throw new Exception("Disconnected occupancy mask");
        Console.WriteLine("Mask: "+m[0].Length+"x"+m.Length+", "+count+" connected occupied cells");
    }
    static void Edge(Dictionary<Point,Point> edges,Point a,Point b) {
        if(edges.ContainsKey(a)) throw new Exception("Diagonal-only boundary contact unsupported");
        edges.Add(a,b);
    }
    static Outline Trace(string[] m) {
        var edges=new Dictionary<Point,Point>();
        for(int y=0;y<m.Length;y++) for(int x=0;x<m[0].Length;x++) if(Occupied(m,x,y)) {
            if(!Occupied(m,x,y-1)) Edge(edges,new Point(x,y),new Point(x+1,y));
            if(!Occupied(m,x+1,y)) Edge(edges,new Point(x+1,y),new Point(x+1,y+1));
            if(!Occupied(m,x,y+1)) Edge(edges,new Point(x+1,y+1),new Point(x,y+1));
            if(!Occupied(m,x-1,y)) Edge(edges,new Point(x,y+1),new Point(x,y));
        }
        Point start=Point.Empty;bool found=false;
        foreach(var p in edges.Keys) if(!found||p.Y<start.Y||p.Y==start.Y&&p.X<start.X){start=p;found=true;}
        var raw=new List<Point>();var current=start;
        do {
            if(raw.Count>edges.Count) throw new Exception("Malformed contour");
            raw.Add(current);current=edges[current];
        }while(current!=start);
        if(raw.Count!=edges.Count) throw new Exception("Holes/multiple contours unsupported");
        var result=new Outline();
        for(int i=0;i<raw.Count;i++) {
            var a=raw[(i+raw.Count-1)%raw.Count];var b=raw[i];var c=raw[(i+1)%raw.Count];
            if((b.X-a.X)*(c.Y-b.Y)-(b.Y-a.Y)*(c.X-b.X)!=0)
                result.Corners.Add(new V(b.X*Cell+Pad,b.Y*Cell+Pad));
        }
        for(int i=0;i<result.Corners.Count;i++) {
            var a=result.Corners[(i+result.Corners.Count-1)%result.Corners.Count];
            var b=result.Corners[i];var c=result.Corners[(i+1)%result.Corners.Count];
            var incoming=(b-a).Unit;var outgoing=(c-b).Unit;
            bool concave=incoming.X*outgoing.Y-incoming.Y*outgoing.X<0;
            result.Concave.Add(concave);if(concave)result.ConcaveCount++;else result.ConvexCount++;
            var begin=b-incoming*Radius;var end=b+outgoing*Radius;
            // Quadratic rounded turn, shared by convex and concave orientations.
            for(int j=0;j<=8;j++) {
                double t=j/8.0;result.Curve.Add(begin*((1-t)*(1-t))+b*(2*(1-t)*t)+end*(t*t));
            }
            var next=c-outgoing*Radius;var direction=next-end;int steps=(int)Math.Ceiling(direction.Length/16);
            var normal=new V(outgoing.Y,-outgoing.X);
            for(int j=1;j<steps;j++) {
                double t=j/(double)steps;var p=end+direction*t;
                // Geometry only: subdued deterministic edge irregularity, never material noise.
                double wobble=Math.Sin(Math.PI*t)*(3.0*Math.Sin((p.X+p.Y*0.7)/37.0)+2.0*Math.Sin((p.X-p.Y)/71.0));
                result.Curve.Add(p+normal*wobble);
            }
        }
        return result;
    }
    static double Smooth(double t){t=Math.Max(0,Math.Min(1,t));return t*t*(3-2*t);}
    static Color Lerp(Color a,Color b,double t) {
        return Color.FromArgb(255,(int)Math.Round(a.R*(1-t)+b.R*t),
            (int)Math.Round(a.G*(1-t)+b.G*t),(int)Math.Round(a.B*(1-t)+b.B*t));
    }
    static void Phase(int x,int length,out int a,out int b,out double mix) {
        int period=length-Overlap;int r=((x%period)+period)%period;
        a=r; b=r;mix=0;
        if(r<Overlap){a=period+r;b=r;mix=Smooth(r/(double)(Overlap-1));}
    }
    static Color Material(int x,int y) {
        int a,b,c,d;double fx,fy;
        Phase(x,Interior.W,out a,out b,out fx);Phase(y,Interior.H,out c,out d,out fy);
        return Lerp(Lerp(Interior.At(a,c),Interior.At(b,c),fx),Lerp(Interior.At(a,d),Interior.At(b,d),fx),fy);
    }
    static Color Strip(Tex src,int along,int across,bool horizontal,bool reverse) {
        int a,b;double blend;Phase(along,horizontal?src.W:src.H,out a,out b,out blend);
        // Register each sample to its actual painted rim, rather than dragging
        // transparent fringe RGB across an artificial straight cutoff.
        int wall=reverse?(horizontal?12:8):2;
        int da=reverse?Math.Min(src.Rim[a],src.Rim[a]-wall-across):Math.Max(src.Rim[a],src.Rim[a]+wall+across);
        int db=reverse?Math.Min(src.Rim[b],src.Rim[b]-wall-across):Math.Max(src.Rim[b],src.Rim[b]+wall+across);
        Color ca=horizontal?src.At(a,da):src.At(da,a);
        Color cb=horizontal?src.At(b,db):src.At(db,b);
        return Lerp(ca,cb,blend);
    }
    // World-facing normals bend the original painted strips around rounded turns.
    // No sprite rotations/flips: north light and south/east sidewalls stay consistent.
    static Color Perimeter(int x,int y,double distance,double nx,double ny) {
        int depth=(int)Math.Round(distance);double sum=0,r=0,g=0,b=0;
        double[] weights={Math.Max(0,-ny),Math.Max(0,ny),Math.Max(0,-nx),Math.Max(0,nx)};
        Color[] colors={Strip(North,x,depth,true,false),Strip(South,x,depth,true,true),
            Strip(West,y,depth,false,false),Strip(East,y,depth,false,true)};
        for(int i=0;i<4;i++){double w=weights[i];sum+=w;r+=colors[i].R*w;g+=colors[i].G*w;b+=colors[i].B*w;}
        return Color.FromArgb(255,(int)Math.Round(r/sum),(int)Math.Round(g/sum),(int)Math.Round(b/sum));
    }
    static Bitmap Render(string[] mask,out Outline outline,bool validate) {
        ValidateMask(mask);outline=Trace(mask);
        int w=mask[0].Length*Cell+Pad*2,h=mask.Length*Cell+Pad*2,size=w*h;
        var dist=new float[size];var nx=new float[size];var ny=new float[size];
        for(int i=0;i<size;i++)dist[i]=float.MaxValue;
        for(int i=0;i<outline.Curve.Count;i++) {
            var a=outline.Curve[i];var b=outline.Curve[(i+1)%outline.Curve.Count];var v=b-a;
            double length2=v.X*v.X+v.Y*v.Y;if(length2<0.001)continue;
            double len=Math.Sqrt(length2);
            int minX=Math.Max(0,(int)Math.Floor(Math.Min(a.X,b.X)-Band)),maxX=Math.Min(w-1,(int)Math.Ceiling(Math.Max(a.X,b.X)+Band));
            int minY=Math.Max(0,(int)Math.Floor(Math.Min(a.Y,b.Y)-Band)),maxY=Math.Min(h-1,(int)Math.Ceiling(Math.Max(a.Y,b.Y)+Band));
            for(int y=minY;y<=maxY;y++)for(int x=minX;x<=maxX;x++) {
                double t=Math.Max(0,Math.Min(1,((x+0.5-a.X)*v.X+(y+0.5-a.Y)*v.Y)/length2));
                double dx=x+0.5-a.X-v.X*t,dy=y+0.5-a.Y-v.Y*t,dd=dx*dx+dy*dy;
                int index=y*w+x;if(dd<dist[index]){dist[index]=(float)dd;nx[index]=(float)(v.Y/len);ny[index]=(float)(-v.X/len);}
            }
        }
        Tex fill;
        using(var matte=New(w,h))using(var g=Graphics.FromImage(matte))using(var path=new GraphicsPath()) {
            var pts=new PointF[outline.Curve.Count];for(int i=0;i<pts.Length;i++)pts[i]=new PointF((float)outline.Curve[i].X,(float)outline.Curve[i].Y);
            path.AddPolygon(pts);g.Clear(Color.Black);g.FillPath(Brushes.White,path);fill=new Tex(matte);
        }
        var pixels=new int[size];
        for(int y=0;y<h;y++)for(int x=0;x<w;x++) {
            int index=y*w+x;bool inside=fill.At(x,y).R>127;
            double d=Math.Sqrt(dist[index])*(inside?1:-1);
            if(!inside&&d < -36)continue;
            var material=Material(x-Pad,y-Pad);
            if(d>Band){pixels[index]=material.ToArgb();continue;}
            double wall=2+10*Math.Max(0,ny[index])+6*Math.Max(0,nx[index]);
            double cover=Smooth((d+wall+0.7)/1.4);
            if(cover<0.001) {
                double shadow=0.18*Math.Exp((d+wall)/7.0)*Smooth((d+36)/10.0);
                pixels[index]=Color.FromArgb((int)Math.Round(shadow*255),12,15,18).ToArgb();continue;
            }
            var painted=Perimeter(x-Pad,y-Pad,d,nx[index],ny[index]);
            var color=Lerp(painted,material,Smooth((d-24)/80.0));
            pixels[index]=Color.FromArgb((int)Math.Round(cover*255),color.R,color.G,color.B).ToArgb();
        }
        var result=New(w,h);var data=result.LockBits(new Rectangle(0,0,w,h),ImageLockMode.WriteOnly,PixelFormat.Format32bppArgb);
        try{for(int y=0;y<h;y++)Marshal.Copy(pixels,y*w,IntPtr.Add(data.Scan0,y*data.Stride),w);}
        finally{result.UnlockBits(data);}
        if(validate)ValidateRaster(mask,pixels,w,h,dist,fill);
        Console.WriteLine("Contour: "+outline.ConvexCount+" convex / "+outline.ConcaveCount+" concave; "+w+"x"+h+" RGBA");
        return result;
    }
    static void ValidateRaster(string[] mask,int[] p,int w,int h,float[] d,Tex fill) {
        for(int i=0;i<p.Length;i++) {
            int alpha=(int)((uint)p[i]>>24);
            if(fill.At(i%w,i/w).R>127&&alpha!=255)throw new Exception("Gap in contour interior");
            if(fill.At(i%w,i/w).R==0&&d[i]>36*36&&alpha!=0)throw new Exception("Stray pixels outside contour");
        }
        ValidateConnectedRaster(p,w,h,1);ValidateConnectedRaster(p,w,h,128);
        for(int y=0;y<mask.Length;y++)for(int x=0;x<mask[0].Length;x++) {
            int alpha=(int)((uint)p[(Pad+y*Cell+Cell/2)*w+Pad+x*Cell+Cell/2]>>24);
            if((alpha==255)!=Occupied(mask,x,y))throw new Exception("Logical cell-center mismatch");
        }
        Console.WriteLine("PASS: mineral and shadow rasters connected; interior opaque; exterior transparent; cell centers match mask");
    }
    static void ValidateConnectedRaster(int[] p,int w,int h,int threshold) {
        int solid=0,first=-1;
        for(int i=0;i<p.Length;i++)if(((uint)p[i]>>24)>=threshold){solid++;first=i;}
        if(first<0)throw new Exception("Empty rendered region");
        var seen=new bool[p.Length];var queue=new Queue<int>();seen[first]=true;queue.Enqueue(first);int reached=0;
        while(queue.Count>0){int i=queue.Dequeue();reached++;int x=i%w,y=i/w;
            int[] candidates={x>0?i-1:-1,x<w-1?i+1:-1,y>0?i-w:-1,y<h-1?i+w:-1};
            foreach(int j in candidates)if(j>=0&&!seen[j]&&((uint)p[j]>>24)>=threshold){seen[j]=true;queue.Enqueue(j);}
        }
        if(reached!=solid)throw new Exception("Disconnected rendered region at alpha threshold "+threshold);
    }
    static void Save(string name,Bitmap image) {
        byte[] raw;using(var s=new MemoryStream()){image.Save(s,ImageFormat.Png);raw=s.ToArray();}
        string path=Path.Combine(Root,name);
        if(Check) {
            if(!File.Exists(path))throw new Exception("Missing "+name);
            byte[] old=File.ReadAllBytes(path);if(old.Length!=raw.Length)throw new Exception("Changed size: "+name);
            for(int i=0;i<raw.Length;i++)if(raw[i]!=old[i])throw new Exception("Changed pixels: "+name);
        }else{Directory.CreateDirectory(Path.GetDirectoryName(path));File.WriteAllBytes(path,raw);}
        Saved++;
    }
    static void Text(Graphics g,string text,int x,int y,int size) {
        using(var f=new Font("Segoe UI",size,FontStyle.Regular,GraphicsUnit.Pixel))
        using(var b=new SolidBrush(Color.FromArgb(224,226,222)))g.DrawString(text,f,b,x,y);
    }
    static Bitmap Overlay(Bitmap art,string[] mask) {
        var b=(Bitmap)art.Clone();using(var g=Graphics.FromImage(b)) {
            using(var fill=new SolidBrush(Color.FromArgb(35,69,224,215)))
            using(var pen=new Pen(Color.FromArgb(185,92,235,222),2))
                for(int y=0;y<mask.Length;y++)for(int x=0;x<mask[0].Length;x++)if(Occupied(mask,x,y)) {
                    var rect=new Rectangle(Pad+x*Cell,Pad+y*Cell,Cell,Cell);g.FillRectangle(fill,rect);g.DrawRectangle(pen,rect);
                }
        }return b;
    }
    static void Panel(Graphics g,Bitmap image,int x,int y,double scale) {
        int w=(int)(image.Width*scale),h=(int)(image.Height*scale);
        using(var brush=new SolidBrush(Color.FromArgb(46,44,39)))g.FillRectangle(brush,x,y,w,h);
        using(var brush=new SolidBrush(Color.FromArgb(51,49,43)))
            for(int yy=0;yy<h;yy+=24)for(int xx=0;xx<w;xx+=24)
                if((xx/24+yy/24)%2==0)g.FillRectangle(brush,x+xx,y+yy,Math.Min(24,w-xx),Math.Min(24,h-yy));
        g.InterpolationMode=InterpolationMode.HighQualityBicubic;g.DrawImage(image,new Rectangle(x,y,w,h));
    }
    static void ExpectRejectedMask(string[] mask,string label) {
        bool rejected=false;
        try{ValidateMask(mask);Trace(mask);}catch(Exception){rejected=true;}
        if(!rejected)throw new Exception("Unsupported mask was accepted: "+label);
        Console.WriteLine("PASS: rejects "+label);
    }
    public static void Run(string root,bool check) {
        Root=root;Check=check;Saved=0;
        Interior=Load("interior");North=Load("north");South=Load("south");West=Load("west");East=Load("east");
        North.PrepareRim(true,false);South.PrepareRim(true,true);West.PrepareRim(false,false);East.PrepareRim(false,true);
        ExpectRejectedMask(new string[]{"#.#"},"disconnected cells");
        ExpectRejectedMask(new string[]{"###","#.#","###"},"hole/multiple contours");
        ExpectRejectedMask(new string[]{"###","#.#","##."},"diagonal boundary contact");
        ExpectRejectedMask(new string[]{"##","#"},"malformed row widths");
        var arts=new Bitmap[3];var overlays=new Bitmap[3];var outlines=new Outline[3];
        for(int i=0;i<3;i++) {
            string[] mask=File.ReadAllLines(Path.Combine(root,"masks/"+IDs[i]+".txt"));
            arts[i]=Render(mask,out outlines[i],true);
            if(outlines[i].ConcaveCount<(i==0?1:2))throw new Exception("Insufficient concave turns");
            overlays[i]=Overlay(arts[i],mask);
            Save("previews/irregular_"+IDs[i]+".png",arts[i]);
            Save("previews/irregular_"+IDs[i]+"_mask.png",overlays[i]);
        }
        var cornerTiles=new Bitmap[8];string[] quadrants={"nw","ne","sw","se"};
        for(int mode=0;mode<2;mode++)for(int q=0;q<4;q++) {
            var rows=new char[][]{new char[]{'.','.'},new char[]{'.','.'}};
            for(int y=0;y<2;y++)for(int x=0;x<2;x++)rows[y][x]=((y*2+x==q) == (mode==0))?'#':'.';
            Outline proof;
            using(var tile=Render(new string[]{new string(rows[0]),new string(rows[1])},out proof,false)) {
                var crop=tile.Clone(new Rectangle(Pad+Cell-96,Pad+Cell-96,192,192),PixelFormat.Format32bppArgb);
                cornerTiles[mode*4+q]=crop;
                Save("components/irregular_"+(mode==0?"convex_":"concave_")+quadrants[q]+".png",crop);
            }
        }
        Bitmap concave=null,stepped=null;
        for(int i=0;i<outlines[0].Corners.Count;i++)if(outlines[0].Concave[i]) {
            var v=outlines[0].Corners[i];concave=arts[0].Clone(new Rectangle((int)v.X-192,(int)v.Y-192,384,384),PixelFormat.Format32bppArgb);break;
        }
        for(int i=0;i<outlines[1].Corners.Count;i++)if(outlines[1].Concave[i]) {
            var v=outlines[1].Corners[i];
            int x=Math.Max(0,Math.Min(arts[1].Width-640,(int)v.X-128));
            int y=Math.Max(0,Math.Min(arts[1].Height-512,(int)v.Y-256));
            stepped=arts[1].Clone(new Rectangle(x,y,640,512),PixelFormat.Format32bppArgb);break;
        }
        Save("previews/irregular_concave_closeup.png",concave);Save("previews/irregular_step_closeup.png",stepped);
        using(var sheet=New(2304,1680))using(var g=Graphics.FromImage(sheet)) {
            g.Clear(Color.FromArgb(24,28,30));
            Text(g,"TLWH / FACETED FERRITE - IRREGULAR ASSEMBLY PROOF",32,24,34);
            Text(g,"Same painted source; reusable oriented perimeter and rounded corner rule. Architecture acceptance pending.",32,72,23);
            int[] positions={32,672,1440};string[] labels={"A / L-SHAPED","B / STEPPED","C / ORGANIC GRID CLUSTER"};
            for(int i=0;i<3;i++) {
                Text(g,labels[i]+" - exact 0.5 source scale",positions[i],116,21);
                Panel(g,arts[i],positions[i],152,0.5);
                Text(g,"Logical occupancy overlay (0.25 scale)",positions[i],790,20);
                Panel(g,overlays[i],positions[i],826,0.25);
            }
            Text(g,"CONCAVE TURN / source-size close-up",32,1160,23);Panel(g,concave,32,1204,1);
            Text(g,"STEPPED PERIMETER / 0.8 source scale",456,1160,23);Panel(g,stepped,456,1204,0.8);
            Text(g,"REUSABLE CORNER TREATMENTS / four world-facing orientations",1032,1160,23);
            for(int mode=0;mode<2;mode++)for(int q=0;q<4;q++) {
                int x=1032+q*280,y=1204+mode*222;
                Panel(g,cornerTiles[mode*4+q],x,y,1);
                Text(g,(mode==0?"convex occupied ":"concave missing ")+quadrants[q],x,y+194,17);
            }
            Text(g,"128 source pixels = 64 world units. Neutral review backdrop only. No Godot execution or gameplay changes.",32,1630,22);
            Save("previews/irregular_contact_sheet.png",sheet);
        }
        foreach(var a in arts)a.Dispose();foreach(var a in overlays)a.Dispose();foreach(var a in cornerTiles)a.Dispose();concave.Dispose();stepped.Dispose();
        Console.WriteLine((check?"CHECK":"BUILD")+" PASS: "+Saved+" irregular proof PNGs. Original rectangular outputs untouched.");
    }
}
'@
[FerriteIrregularProof]::Run($PSScriptRoot,[bool]$Check)
