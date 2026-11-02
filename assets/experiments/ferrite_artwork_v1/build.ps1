param([switch]$Check)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
# Windows/.NET offline compositor. No engine, shell subprocesses, or dependencies.
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.IO;
using System.Drawing;
using System.Drawing.Imaging;
using System.Drawing.Drawing2D;
using System.Security.Cryptography;
using System.Collections.Generic;

public static class FerritePrototypeV1 {
    static string Root;
    static bool Check;
    static int Count;
    const int Pad = 64, Cap = 192, Blend = 96;
    static readonly string[] Names = {"north_west", "north", "north_east",
        "west", "interior", "east", "south_west", "south", "south_east"};
    static Bitmap[,] Parts = new Bitmap[3,3];
    static Bitmap New(int w, int h) { return new Bitmap(w,h,PixelFormat.Format32bppArgb); }
    static Graphics GraphicsFor(Bitmap b) {
        var g=Graphics.FromImage(b); g.CompositingMode=CompositingMode.SourceOver;
        g.InterpolationMode=InterpolationMode.HighQualityBicubic;
        g.PixelOffsetMode=PixelOffsetMode.HighQuality; return g;
    }
    static Bitmap Crop(Bitmap b,int x,int y,int w,int h) {
        return b.Clone(new Rectangle(x,y,w,h),PixelFormat.Format32bppArgb);
    }
    static byte[] Png(Bitmap b) {
        using(var s=new MemoryStream()) { b.Save(s,ImageFormat.Png); return s.ToArray(); }
    }
    static void Save(string path, Bitmap b) {
        var bytes=Png(b); var full=Path.Combine(Root,path);
        if(Check) {
            if(!File.Exists(full)) throw new Exception("Missing "+path);
            var previous=File.ReadAllBytes(full);
            if(previous.Length!=bytes.Length) throw new Exception("Different size: "+path);
            for(int i=0;i<bytes.Length;i++) if(bytes[i]!=previous[i])
                throw new Exception("Nonreproducible: "+path);
        } else {
            Directory.CreateDirectory(Path.GetDirectoryName(full));
            // Only fixed derived paths are written. Source master is never changed.
            File.WriteAllBytes(full,bytes);
        }
        Count++;
    }
    // Native-pixel splice: retain both endpoints, overlap two source intervals.
    // No scaling of art. Contraction removes material; extension repeats an overlap.
    static void Axis(int t,int source,int target,out int a,out int b,out double mix) {
        if(source==target) { a=b=t; mix=0; return; }
        int start=(target-Blend)/2;
        a=Math.Max(0,Math.Min(source-1,t));
        b=Math.Max(0,Math.Min(source-1,t+source-target));
        mix=Math.Max(0,Math.Min(1,(t-start)/(double)(Blend-1)));
        mix=mix*mix*(3-2*mix);
    }
    static Color Mix(Color a,Color b,double t) {
        double aa=a.A*(1-t), ba=b.A*t, alpha=aa+ba;
        if(alpha<0.5) return Color.FromArgb(0,0,0,0);
        return Color.FromArgb((int)Math.Round(alpha),
            (int)Math.Round((a.R*aa+b.R*ba)/alpha),
            (int)Math.Round((a.G*aa+b.G*ba)/alpha),
            (int)Math.Round((a.B*aa+b.B*ba)/alpha));
    }
    static Bitmap Fit(Bitmap src,int w,int h) {
        if(w<Blend || h<Blend || w>2*src.Width-Blend || h>2*src.Height-Blend)
            throw new Exception("Unsupported splice dimensions");
        var result=New(w,h);
        for(int y=0;y<h;y++) {
            int ya,yb; double fy; Axis(y,src.Height,h,out ya,out yb,out fy);
            for(int x=0;x<w;x++) {
                int xa,xb; double fx; Axis(x,src.Width,w,out xa,out xb,out fx);
                result.SetPixel(x,y,Mix(Mix(src.GetPixel(xa,ya),src.GetPixel(xb,ya),fx),
                    Mix(src.GetPixel(xa,yb),src.GetPixel(xb,yb),fx),fy));
            }
        }
        return result;
    }
    static Bitmap Assemble(int cellsX,int cellsY) {
        int w=cellsX*128+Pad*2,h=cellsY*128+Pad*2;
        int[] widths={Cap,w-Cap*2,Cap}, heights={Cap,h-Cap*2,Cap};
        var result=New(w,h);
        using(var g=GraphicsFor(result)) {
            g.CompositingMode=CompositingMode.SourceCopy;
            int y=0;
            for(int row=0;row<3;row++) {
                int x=0;
                for(int col=0;col<3;col++) {
                    using(var part=Fit(Parts[row,col],widths[col],heights[row]))
                        g.DrawImageUnscaled(part,x,y);
                    x+=widths[col];
                }
                y+=heights[row];
            }
        }
        // Interior must contain no transparency gaps, including every component join.
        for(int y=Pad+24;y<h-Pad-24;y++)
            for(int x=Pad+24;x<w-Pad-24;x++)
                if(result.GetPixel(x,y).A!=255) throw new Exception("Interior alpha gap at "+x+","+y+": "+result.GetPixel(x,y).A);
        if(result.GetPixel(0,0).A!=0) throw new Exception("Missing outside transparency");
        return result;
    }
    static Bitmap Backdrop(Bitmap art) {
        var b=New(art.Width,art.Height);
        using(var g=GraphicsFor(b)) {
            g.Clear(Color.FromArgb(45,43,38));
            using(var brush=new SolidBrush(Color.FromArgb(49,48,42)))
                for(int y=0;y<b.Height;y+=32) for(int x=0;x<b.Width;x+=32)
                    if((x/32+y/32)%2==0) g.FillRectangle(brush,x,y,32,32);
            g.DrawImageUnscaled(art,0,0);
        }
        return b;
    }
    static void Text(Graphics g,string text,float x,float y,int size,Color color) {
        using(var f=new Font("Segoe UI",size,FontStyle.Regular,GraphicsUnit.Pixel))
        using(var b=new SolidBrush(color)) g.DrawString(text,f,b,x,y);
    }
    static void Panel(Graphics g,Bitmap art,int x,int y,int w,int h) {
        double scale=Math.Min(w/(double)art.Width,h/(double)art.Height);
        using(var bg=Backdrop(art))
            g.DrawImage(bg,new Rectangle(x,y,(int)(art.Width*scale),(int)(art.Height*scale)));
    }
    public static void Run(string root,bool check) {
        Root=root; Check=check; Count=0;
        using(var original=new Bitmap(Path.Combine(root,"source/ferrite_master.png"))) {
            if(original.Width!=1619 || original.Height!=972) throw new Exception("Wrong master dimensions");
            // Master logical rectangle: (96,160)..(1536,832). Transparent margin 64.
            // Preserve the source file; normalize only tiny generator alpha residue.
            using(var source=Crop(original,32,96,1568,800)) {
                for(int y=0;y<source.Height;y++) for(int x=0;x<source.Width;x++) {
                    var p=source.GetPixel(x,y);
                    int alpha=p.A<=8?0:(p.A>=240?255:p.A);
                    // AI alpha has pinholes on solid mineral. Seal only the safe
                    // interior, 24px inside the logical rectangle; keep edge alpha.
                    if(x>=Pad+24 && x<source.Width-Pad-24 &&
                        y>=Pad+24 && y<source.Height-Pad-24) alpha=255;
                    source.SetPixel(x,y,alpha==0?Color.FromArgb(0,0,0,0):Color.FromArgb(alpha,p.R,p.G,p.B));
                }
                int[] xs={0,Cap,source.Width-Cap,source.Width};
                int[] ys={0,Cap,source.Height-Cap,source.Height};
                for(int row=0;row<3;row++) for(int col=0;col<3;col++) {
                    var piece=Crop(source,xs[col],ys[row],xs[col+1]-xs[col],ys[row+1]-ys[row]);
                    Parts[row,col]=piece; Save("components/"+Names[row*3+col]+".png",piece);
                }
                // Complementary material samples, not independent seamless overlay promises.
                using(var silver=Crop(source,256,160,256,256)) Save("components/surface_silver.png",silver);
                using(var quiet=Crop(source,768,224,256,256)) Save("components/surface_quiet.png",quiet);
            }
        }
        using(var medium=Assemble(6,4)) using(var large=Assemble(10,6)) {
            Save("previews/medium_6x4.png",medium); Save("previews/large_10x6.png",large);
            using(var scale=(Bitmap)large.Clone()) {
                using(var g=GraphicsFor(scale)) {
                    using(var line=new Pen(Color.FromArgb(100,226,214,170),1)) {
                        for(int x=Pad;x<=Pad+1280;x+=128) g.DrawLine(line,x,Pad,x,Pad+768);
                        for(int y=Pad;y<=Pad+768;y+=128) g.DrawLine(line,Pad,y,Pad+1280,y);
                    }
                    var footprint=new Rectangle(Pad+384,Pad+256,128,128);
                    using(var fill=new SolidBrush(Color.FromArgb(70,102,233,222))) g.FillRectangle(fill,footprint);
                    using(var pen=new Pen(Color.FromArgb(255,102,233,222),3)) g.DrawRectangle(pen,footprint);
                    Text(g,"64 x 64 world units / 2 x 2 construction cells",Pad+32,Pad+704,23,Color.White);
                }
                Save("previews/large_10x6_scale.png",scale);
            }
            using(var surface=Crop(large,256,192,384,256))
            using(var edge=Crop(large,768,large.Height-176,384,160))
            using(var sheet=New(1800,1510)) using(var g=GraphicsFor(sheet)) {
                g.Clear(Color.FromArgb(24,28,30));
                Text(g,"TLWH  /  FACETED FERRITE",36,24,34,Color.FromArgb(232,222,197));
                Text(g,"Prototype v1 - owner visual acceptance pending",38,72,22,Color.FromArgb(172,186,190));
                Text(g,"MEDIUM  /  6 x 4 terrain cells - 384 x 256 world units",36,118,22,Color.White);
                Panel(g,medium,36,155,680,486);
                Text(g,"LARGE  /  10 x 6 terrain cells - 640 x 384 world units",760,118,22,Color.White);
                Panel(g,large,760,155,1004,640);
                Text(g,"REUSABLE FAMILY  /  native density, overlap-spliced center",36,662,22,Color.White);
                for(int row=0;row<3;row++) for(int col=0;col<3;col++) {
                    int x=36+col*220,y=702+row*164;
                    Panel(g,Parts[row,col],x,y,208,128);
                    Text(g,Names[row*3+col],x,y+132,17,Color.FromArgb(190,201,203));
                }
                Text(g,"MATERIAL  /  surface close-up",760,830,22,Color.White);
                Panel(g,surface,760,870,580,385);
                Text(g,"SHALLOW PERIMETER  /  painted contact shading",36,1230,22,Color.White);
                Panel(g,edge,36,1270,680,220);
                Text(g,"SCALE  /  cyan = existing Extractor footprint",1370,830,19,Color.White);
                using(var thumb=(Bitmap)large.Clone()) {
                    using(var tg=GraphicsFor(thumb)) using(var pen=new Pen(Color.Cyan,5))
                        tg.DrawRectangle(pen,Pad+384,Pad+256,128,128);
                    Panel(g,thumb,1370,870,394,300);
                }
                using(var silver=new Bitmap(Path.Combine(root,"components/surface_silver.png")))
                using(var quiet=new Bitmap(Path.Combine(root,"components/surface_quiet.png"))) {
                    Panel(g,silver,1370,1200,184,184);
                    Panel(g,quiet,1570,1200,184,184);
                    Text(g,"silver sample",1370,1392,17,Color.White);
                    Text(g,"quiet sample",1570,1392,17,Color.White);
                }
                Text(g,"128 source pixels = 64 world units",760,1300,24,Color.FromArgb(232,222,197));
                Text(g,"Clean previews retain transparency. Checkerboard is review-only.",760,1340,20,Color.FromArgb(172,186,190));
                Text(g,"No gameplay integration. No Godot execution.",760,1376,20,Color.FromArgb(172,186,190));
                Save("previews/contact_sheet.png",sheet);
            }
        }
        foreach(var p in Parts) p.Dispose();
        Console.WriteLine((check?"CHECK PASS: ":"BUILD PASS: ")+Count+" deterministic PNG outputs; alpha, dimensions, interior joins, 128px footprint.");
    }
}
'@
[FerritePrototypeV1]::Run($PSScriptRoot, [bool]$Check)
