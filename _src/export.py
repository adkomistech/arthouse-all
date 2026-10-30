from PIL import Image
pick={"hennessy-residence":("hen_res",3),"hennessy-villa":("hen_villa",3),"above-condominium":("ae_condo",13),
"above-villa":("ae_villa",14),"above-residence":("ae_res",1),"palmetto-park":("pal_park",1),"proud-residence":("proud",1),
"proud-rawai":("rawai",4),"palmetto-condo":("pal_condo",3),"fifth-element":("fifth",3)}
for name,(k,i) in pick.items():
    f=open(f"cand/{k}.txt",encoding="utf-8").read().split("\n")[i]
    im=Image.open(f).convert("RGB"); w,h=im.size
    # crop to 4:3 centered
    tr=4/3
    if w/h>tr: nw=int(h*tr); im=im.crop(((w-nw)//2,0,(w-nw)//2+nw,h))
    else: nh=int(w/tr); im=im.crop((0,(h-nh)//2,w,(h-nh)//2+nh))
    im=im.resize((1000,750),Image.LANCZOS)
    im.save(f"site/img/{name}.webp","WEBP",quality=74,method=6)
    print(name,f.split("/")[-1])
