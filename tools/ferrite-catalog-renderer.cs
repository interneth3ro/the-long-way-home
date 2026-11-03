// Offline adapter to the preserved PR #123 compositors; never a game dependency.
using System;
using System.IO;
using System.Drawing;
using System.Drawing.Imaging;
using System.Drawing.Drawing2D;
using System.Reflection;

public static class FerriteCatalogRenderer {
    static Type Irregular;
    const BindingFlags PrivateStatic = BindingFlags.NonPublic | BindingFlags.Static;
    static object Call(Type type, string name, params object[] args) {
        var method = type.GetMethod(name, PrivateStatic);
        if (method == null) throw new Exception("Missing preserved compositor method: " + name);
        return method.Invoke(null, args);
    }
    static void Field(Type type, string name, object value) {
        var field = type.GetField(name, PrivateStatic);
        if (field == null) throw new Exception("Missing preserved compositor field: " + name);
        field.SetValue(null, value);
    }
    public static void Initialize(Type irregular, string root) {
        Irregular = irregular;
        string prototype = Path.Combine(root, "assets/experiments/ferrite_artwork_v1");
        Field(Irregular, "Root", prototype);
        string[] edges = {"Interior", "North", "South", "West", "East"};
        foreach (string edge in edges) {
            object texture = Call(Irregular, "Load", edge.ToLowerInvariant());
            Field(Irregular, edge, texture);
            if (edge != "Interior") texture.GetType().GetMethod("PrepareRim").Invoke(texture,
                new object[] {edge == "North" || edge == "South", edge == "South" || edge == "East"});
        }
    }
    public static Bitmap Render(string[] mask) {
        Bitmap image = (Bitmap)Call(Irregular, "Render", new object[] {mask, null, true});
        try {
            if (image.Width != mask[0].Length*128+128 || image.Height != mask.Length*128+128)
                throw new Exception("Incorrect padded image dimensions");
            for (int y=0; y<mask.Length; y++) for (int x=0; x<mask[y].Length; x++) {
                int alpha = image.GetPixel(64+x*128+64, 64+y*128+64).A;
                if ((mask[y][x]=='#' && alpha!=255) || (mask[y][x]=='.' && alpha!=0))
                    throw new Exception("Rendered cell-center registration mismatch");
            }
            // Check outer transparency, including entire canvas borders.
            for (int x=0; x<image.Width; x++)
                if (image.GetPixel(x,0).A!=0 || image.GetPixel(x,image.Height-1).A!=0)
                    throw new Exception("Paint reaches horizontal canvas border");
            for (int y=0; y<image.Height; y++)
                if (image.GetPixel(0,y).A!=0 || image.GetPixel(image.Width-1,y).A!=0)
                    throw new Exception("Paint reaches vertical canvas border");
            // Render(..., true) already checks opaque interior, far exterior
            // and raster connectivity at alpha thresholds 1 and 128.
            return image;
        } catch {image.Dispose(); throw;}
    }
    public static void Save(string path, Bitmap image, bool check) {
        byte[] bytes;
        using (var stream = new MemoryStream()) {image.Save(stream, ImageFormat.Png); bytes=stream.ToArray();}
        if (check) {
            byte[] previous=File.ReadAllBytes(path);
            if (previous.Length!=bytes.Length) throw new Exception("Nonreproducible PNG length: " + path);
            for (int i=0; i<bytes.Length; i++) if (previous[i]!=bytes[i])
                throw new Exception("Nonreproducible PNG bytes: " + path);
        } else {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            File.WriteAllBytes(path,bytes);
        }
    }
    static void Text(Graphics g, string text, int x, int y, int size) {
        using (var font=new Font("Segoe UI",size,FontStyle.Regular,GraphicsUnit.Pixel))
        using (var brush=new SolidBrush(Color.FromArgb(225,229,231))) g.DrawString(text,font,brush,x,y);
    }
    static void Panel(Graphics g, Bitmap image, int x, int y) {
        int width=(int)(image.Width*0.3), height=(int)(image.Height*0.3);
        using (var brush=new SolidBrush(Color.FromArgb(49,47,42))) g.FillRectangle(brush,x,y,width,height);
        using (var brush=new SolidBrush(Color.FromArgb(55,53,47)))
            for (int yy=0; yy<height; yy+=16) for (int xx=0; xx<width; xx+=16)
                if ((xx/16+yy/16)%2==0) g.FillRectangle(brush,x+xx,y+yy,Math.Min(16,width-xx),Math.Min(16,height-yy));
        g.InterpolationMode=InterpolationMode.HighQualityBicubic;
        g.DrawImage(image,new Rectangle(x,y,width,height));
    }
    public static void ContactSheet(Bitmap[] images, string[] ids, string[] sizes, string[] families, string directory, bool check) {
        using (var sheet=new Bitmap(1740,2400,PixelFormat.Format32bppArgb))
        using (var g=Graphics.FromImage(sheet)) {
            g.Clear(Color.FromArgb(24,28,30));
            Text(g,"TLWH / FACETED FERRITE CATALOG V1 - 10 CANDIDATES",28,20,30);
            Text(g,"Owner artistic acceptance pending. All panels use 0.30 source scale; gameplay density is 0.50.",28,64,22);
            Text(g,"Preserved painted lighting; no rotated/mirrored deposits. Clean PNGs retain transparency.",28,96,20);
            int sectionY=148;
            foreach (string size in new string[] {"small","medium","large"}) {
                Text(g,size.ToUpperInvariant(),28,sectionY,26);
                int slot=0;
                for (int i=0; i<images.Length; i++) if (sizes[i]==size) {
                    int x=28+(slot%3)*570, y=sectionY+42+(slot/3)*400;
                    Text(g,ids[i],x,y,19);
                    Text(g,families[i]+" / "+((images[i].Width-128)/128)+"x"+((images[i].Height-128)/128)+" cells",x,y+24,18);
                    Panel(g,images[i],x,y+54);slot++;
                }
                sectionY+=60+((slot+2)/3)*400;
            }
            Text(g,"Known source limits: recurring silver highlights/diagonal grain; more regular concave rims. No in-game verification.",28,2360,19);
            Save(Path.Combine(directory,"contact_sheet.png"),sheet,check);
        }
    }
    public static void Overlay(Bitmap image, string[] mask, string path, bool check) {
        using (var overlay=(Bitmap)image.Clone()) using (var g=Graphics.FromImage(overlay)) {
            using (var fill=new SolidBrush(Color.FromArgb(35,69,224,215)))
            using (var pen=new Pen(Color.FromArgb(205,92,235,222),2))
                for (int y=0; y<mask.Length; y++) for (int x=0; x<mask[y].Length; x++) if (mask[y][x]=='#') {
                    var cell=new Rectangle(64+x*128,64+y*128,128,128);
                    g.FillRectangle(fill,cell);g.DrawRectangle(pen,cell);
                }
            bool found=false;
            for (int y=0; y<mask.Length-1 && !found; y++) for (int x=0; x<mask[0].Length-1 && !found; x++)
                if (mask[y][x]=='#' && mask[y][x+1]=='#' && mask[y+1][x]=='#' && mask[y+1][x+1]=='#') {
                    using (var fill=new SolidBrush(Color.FromArgb(65,255,213,92)))
                    using (var pen=new Pen(Color.FromArgb(255,255,213,92),4)) {
                        // Exactly ONE terrain cell: 128 source px = 64 world units.
                        var footprint=new Rectangle(64+x*128,64+y*128,128,128);
                        g.FillRectangle(fill,footprint);g.DrawRectangle(pen,footprint);
                    }
                    found=true;
                }
            if (!found) throw new Exception("No broad Extractor placement region");
            Text(g,"Cyan: logical mask / Yellow: 64x64 world-unit Extractor",10,12,16);
            Save(path,overlay,check);
        }
    }
}
