# -*- coding: utf-8 -*-
import os, math, threading, requests, struct, wave, re, xml.etree.ElementTree as ET
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.core.audio import SoundLoader
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.scrollview import ScrollView

H={"User-Agent":"Mozilla/5.0"}; FAV="favoriler.txt"; LOG="borsa_sonuc.txt"; OUT=[]
def yaz(*x): OUT.append(" ".join(map(str,x)))
def sym(h): return (h[3:],True) if h.startswith("US_") else (h+".IS",False)
def veri(s,r="5y",i="1mo"):
    q=requests.get("https://query1.finance.yahoo.com/v8/finance/chart/"+s,params={"range":r,"interval":i},headers=H,timeout=25);q.raise_for_status()
    c=q.json()["chart"]
    if c.get("error") or not c.get("result"): raise ValueError("Yahoo Finance veri döndürmedi.")
    z=c["result"][0];ts=z.get("timestamp") or [];ks=z["indicators"]["quote"][0].get("close") or []
    a=[(datetime.fromtimestamp(t),float(k)) for t,k in zip(ts,ks) if k is not None]
    if not a: raise ValueError("Fiyat verisi yok.")
    return a
def risk(fs):
    if len(fs)<2:return 0,0,"VERİ YETERSİZ",0
    r=[(fs[i]/fs[i-1]-1)*100 for i in range(1,len(fs)) if fs[i-1]>0]
    if not r:return 0,0,"VERİ YETERSİZ",0
    m=sum(r)/len(r);v=(sum((x-m)**2 for x in r)/len(r))**.5;peak=fs[0];dd=0
    for x in fs:peak=max(peak,x);dd=min(dd,(x/peak-1)*100)
    return v,dd,"DÜŞÜK" if v<8 and dd>-25 else "ORTA" if v<15 and dd>-45 else "YÜKSEK",m
def favread():
    try:
        with open(FAV,encoding="utf8") as f:return [x.strip() for x in f if x.strip()]
    except:return []
def favwrite(x):
    with open(FAV,"w",encoding="utf8") as f:f.write("\n".join(x))
def analiz(hs):
    rows=[]
    for h in hs:
        try:
            fs=[x for _,x in veri(sym(h)[0])[0:]]
            total=(fs[-1]/fs[0]-1)*100;v,d,r,m=risk(fs)
            annual=((1+m/100)**12-1)*100;sd=v*math.sqrt(12)
            yaz("\n===",h,"===","5 yıllık toplam %",round(total,1),"Oynaklık %",round(v,1),"En büyük düşüş %",round(d,1),"Risk",r)
            yaz("Geçmişe göre kaba 1 yıllık aralık %",round(max(-100,annual-sd)),"ile %",round(annual+sd))
            rows.append((h,total,r,d))
        except Exception as e:yaz(h,"analiz edilemedi:",e)
    for i,x in enumerate(sorted(rows,key=lambda a:a[1],reverse=True),1):yaz(i,x[0],"getiri %",round(x[1],1),"risk",x[2])
    if rows:
        try:
            with open(LOG,"a",encoding="utf8") as f:
                f.write("\n"+datetime.now().strftime("%d.%m.%Y %H:%M")+"\n")
                for x in rows:f.write(str(x)+"\n")
        except Exception as e:yaz("Kayıt hatası:",e)
def avg(x):return sum(x)/len(x) if x else 0
def ema(x,n):
    if len(x)<n:return []
    a=2/(n+1);o=[avg(x[:n])]
    for z in x[n:]:o.append(z*a+o[-1]*(1-a))
    return o
def rsi(x,n=14):
    if len(x)<=n:return None
    d=[x[i]-x[i-1] for i in range(1,len(x))]
    u=avg([max(z,0) for z in d[-n:]]);v=avg([max(-z,0) for z in d[-n:]])
    return 100 if v==0 else 100-100/(1+u/v)
def bb(x):
    if len(x)<20:return None
    a=x[-20:];m=avg(a);s=math.sqrt(avg([(z-m)**2 for z in a]));return m,m+2*s,m-2*s
def macd(x):
    a,b=ema(x,12),ema(x,26)
    if not b:return None
    line=[a[i+len(a)-len(b)]-b[i] for i in range(len(b))];sig=ema(line,9)
    return (line[-1],sig[-1],line[-1]-sig[-1]) if sig else None
def forecast(x,n):
    if len(x)<30:return None
    r=[math.log(x[i]/x[i-1]) for i in range(1,len(x)) if x[i]>0 and x[i-1]>0][-60:]
    if len(r)<20:return None
    m=max(-.02,min(.02,avg(r)));s=math.sqrt(avg([(z-m)**2 for z in r]));p=x[-1]
    up=max(5,min(95,50+m/(s+.0001)*12))
    return p*math.exp(m*n),p*math.exp((m-1.5*s)*math.sqrt(n)),p*math.exp((m+1.5*s)*math.sqrt(n)),up,100-up
def backtest(x,n=7):
    good=total=0
    for i in range(max(80,len(x)-300),len(x)-n-1,5):
        t=forecast(x[:i],n)
        if t:good+=((t[0]>=x[i])==(x[i+n]>=x[i]));total+=1
    return (good/total*100,total) if total else None
def yz(h):
    try:
        x=[v for _,v in veri(sym(h)[0],"2y","1d")]
        if len(x)<60:raise ValueError("En az 60 günlük veri gerekli.")
        p=x[-1];score=0;v=rsi(x);m=macd(x);b=bb(x)
        yaz("\n===== YZ ANALİZ:",h,"=====","Son fiyat:",round(p,3))
        if v is not None:
            yaz("RSI:",round(v,2));score+=1 if v<30 else -1 if v>70 else 0
        if m:
            yaz("MACD:",round(m[0],4),"Sinyal:",round(m[1],4));score+=1 if m[2]>0 else -1
        if b:
            yaz("Bollinger alt/orta/üst:",round(b[2],3),round(b[0],3),round(b[1],3));score+=1 if p<b[2] else -1 if p>b[1] else 0
        for n in (20,50,200):
            e=ema(x,n)
            if e:yaz("EMA"+str(n)+":",round(e[-1],3));score+=1 if p>e[-1] else -1
        yaz("Destek:",round(min(x[-60:]),3),"Direnç:",round(max(x[-60:]),3))
        yaz("BİRLEŞİK SİNYAL:","AL" if score>=3 else "SAT" if score<=-3 else "BEKLE","puan",score)
        for n in (7,30,90):
            t=forecast(x,n)
            if t:yaz(n,"gün beklenen",round(t[0],3),"aralık",round(t[1],3),"-",round(t[2],3),"yükseliş %",round(t[3]),"düşüş %",round(t[4]))
        t=backtest(x)
        yaz("Geçmiş 7 günlük yön testi:",(str(round(t[0],1))+"% / "+str(t[1])+" örnek") if t else "yetersiz veri")
        yaz("İstatistiksel senaryodur; kesin tahmin veya yatırım tavsiyesi değildir.")
    except Exception as e:yaz(h,"YZ analizi yapılamadı:",e)
def bilanco(h):
    if h.startswith("US_"):yaz(h,"bilançosu desteklenmiyor.");return
    try:
        import borsapy as bp
        t=bp.Ticker(h);bs=t.balance_sheet;gs=t.income_stmt
        if callable(bs):bs=bs()
        if callable(gs):gs=gs()
        def get(df,keys):
            for key in keys:
                for i,name in enumerate(df.index):
                    n=str(name).lower().replace("ı","i").replace("ş","s").replace("ğ","g").replace("ü","u").replace("ö","o").replace("ç","c")
                    if key in n:
                        try:return float(df.iloc[i,0])
                        except:pass
        var=get(bs,["toplam varlik"]);oz=get(bs,["toplam ozkaynak","ozkaynaklar"]);don=get(bs,["donen varlik"]);kisa=get(bs,["kisa vadeli yukumluluk"])
        satis=get(gs,["satis gelirleri","hasilat"]);net=get(gs,["donem net kar","net kar"])
        yaz("\n===",h,"BİLANÇO===")
        for n,v in (("Varlıklar",var),("Özkaynak",oz),("Satış",satis),("Net kâr",net)):yaz(n,round(v/1e9,2) if v is not None else "veri yok","milyar")
        count=weak=0
        if var is not None and oz is not None and oz>0:
            count+=1;q=(var-oz)/oz;yaz("Borç/özkaynak benzeri oran:",round(q,2));weak+=q>=2.5
        if don is not None and kisa and kisa>0:
            count+=1;q=don/kisa;yaz("Cari oran:",round(q,2));weak+=q<1
        if net is not None and satis and satis>0:
            count+=1;q=net/satis*100;yaz("Net kâr marjı %",round(q,1));weak+=q<0
        yaz("GENEL GÖRÜNÜM:","HESAPLANAMADI" if not count else "SAĞLAM" if not weak else "DİKKAT/ZAYIF")
    except Exception as e:yaz(h,"bilanço alınamadı:",e)
def portfolio(text):
    pos=[]
    for line in text.splitlines():
        p=line.upper().split()
        if len(p)>=2:
            try:pos.append((p[0],float(p[1].replace(",",".")),float(p[2].replace(",",".")) if len(p)>2 else None))
            except:yaz("Hatalı satır:",line)
    if not pos:yaz("Örnek: THYAO 100 250");return
    fx=None
    if any(h.startswith("US_") for h,_,_ in pos):
        try:fx=veri("TRY=X","5d","1d")[-1][1];yaz("Dolar/TL:",round(fx,2))
        except:yaz("Kur alınamadı.")
    rows=[]
    for h,n,b in pos:
        try:
            _,us=sym(h);p=veri(sym(h)[0],"5d","1d")[-1][1]
            if us and fx is None:continue
            mult=fx if us else 1;rows.append((h,n,b,p,n*p*mult,mult))
        except Exception as e:yaz(h,"alınamadı:",e)
    total=sum(z[4] for z in rows)
    for h,n,b,p,val,m in rows:
        yaz(h,"fiyat",round(p,2),"değer",round(val,2),"TL | pay %",round(val/total*100,1))
        if b:yaz("Alıştan beri kâr/zarar %",round((p/b-1)*100,1))
    if rows:yaz("Toplam portföy:",round(total,2),"TL")


BIST_HEATMAP = ["THYAO","GARAN","AKBNK","ISCTR","YKBNK","KCHOL","SAHOL","ASELS",
                "TUPRS","BIMAS","EREGL","SISE","FROTO","TOASO","TCELL","TAVHL",
                "PGSUS","KOZAL","ENKAI","PETKM"]
POS_WORDS = ("profit","growth","record","upgrade","dividend","strong","positive","beat","surge",
             "kar","büyüme","rekor","temettü","güçlü","olumlu","artış","anlaşma","yatırım")
NEG_WORDS = ("loss","decline","downgrade","debt","fine","weak","negative","miss","fall","drop",
             "zarar","düşüş","borç","ceza","zayıf","olumsuz","azalış","soruşturma","iptal")

def haber_analiz(h):
    """Yahoo Finance arama haberlerini dener; gerekirse RSS akışına düşer."""
    try:
        ticker = h if h.startswith("US_") else h + ".IS"
        items = []
        # Önce Yahoo Finance arama servisi.
        try:
            r = requests.get(
                "https://query1.finance.yahoo.com/v1/finance/search",
                params={"q": ticker, "newsCount": 12, "quotesCount": 0},
                headers=H, timeout=15
            )
            if r.ok:
                items = r.json().get("news", []) or []
        except Exception:
            items = []

        # Arama servisi haber döndürmezse Yahoo RSS akışını dene.
        if not items:
            rss_url = "https://feeds.finance.yahoo.com/rss/2.0/headline"
            r = requests.get(
                rss_url,
                params={"s": ticker, "region": "US", "lang": "en-US"},
                headers=H, timeout=15
            )
            r.raise_for_status()
            root = ET.fromstring(r.content)
            for node in root.findall(".//item")[:12]:
                items.append({
                    "title": node.findtext("title", default=""),
                    "publisher": "Yahoo Finance RSS",
                    "link": node.findtext("link", default="")
                })

        if not items:
            yaz(h, "için şu anda haber bulunamadı. Daha sonra tekrar dene.")
            return

        yaz("\\n===== HABER ANALİZİ:", h, "=====")
        pos = neg = neutral = 0
        for item in items[:10]:
            title = str(item.get("title", "")).strip()
            publisher = str(item.get("publisher", "Yahoo Finance"))
            low = title.lower()
            ps = sum(w in low for w in POS_WORDS)
            ns = sum(w in low for w in NEG_WORDS)
            if ps > ns:
                label = "OLUMLU"; pos += 1
            elif ns > ps:
                label = "OLUMSUZ"; neg += 1
            else:
                label = "NÖTR"; neutral += 1
            yaz("•", label, "|", title, "|", publisher)
            if item.get("link"):
                yaz("Haber:", item["link"])
        yaz("Haber dağılımı: olumlu", pos, "| olumsuz", neg, "| nötr", neutral)
        yaz("Not: Başlık temelli otomatik sınıflandırmadır; haberin tamamını ve bağlamını değerlendirmez.")
    except Exception as e:
        yaz(h, "haberleri alınamadı:", str(e))
        yaz("İnternet bağlantısını kontrol et veya birkaç dakika sonra tekrar dene.")

def piyasa_haritasi():
    rows=[]
    yaz("===== BIST PİYASA ISI HARİTASI =====")
    for h in BIST_HEATMAP:
        try:
            data=veri(h+".IS","5d","1d")
            if len(data)>=2 and data[-2][1]>0:
                rows.append((h,(data[-1][1]/data[-2][1]-1)*100,data[-1][1]))
        except Exception:pass
    rows.sort(key=lambda z:z[1],reverse=True)
    if not rows:
        yaz("Piyasa verisi alınamadı. İnternet bağlantısını kontrol et.");return
    for h,ch,price in rows:
        icon="🟩" if ch>=2 else "🟢" if ch>0 else "🟥" if ch<=-2 else "🔴" if ch<0 else "⬜"
        yaz(icon,h,"%+.2f%%"%ch,"fiyat",round(price,2))
    yaz("Yeşil yükseliş, kırmızı düşüş demektir. Son işlem günü verisidir.")

def akilli_sohbet(mesaj):
    parts = [x.strip("?,.!:;()") for x in mesaj.upper().split()]
    stop = {"BUGUN","BUGÜN","NASIL","MI","MU","Mİ","MÜ","RISKLI","RİSKLİ",
            "HAKKINDA","YORUM","YAP","ANALIZ","ANALİZ","HISSE","HİSSE",
            "RISK","RİSK","DURUMU","NE","OLUR","SENCE"}
    h = next((x for x in parts
              if x not in stop and re.fullmatch(r"(US_[A-Z0-9.-]+|[A-Z]{3,8})", x)), None)
    if not h:
        yaz("Bir hisse kodu yaz. Örnek: THYAO bugün nasıl? veya AKBNK riskli mi?")
        return
    try:
        x=[v for _,v in veri(sym(h)[0],"2y","1d")]
        if len(x)<60:raise ValueError("Yeterli fiyat geçmişi yok.")
        price=x[-1];rv=rsi(x);mc=macd(x);e20=ema(x,20);e50=ema(x,50)
        vol,dd,level,_=risk(x[-252:]);score=0
        yaz("===== AKILLI PİYASA ASİSTANI =====")
        yaz(h,"son fiyat:",round(price,3))
        if rv is not None:
            score+=1 if rv<35 else -1 if rv>70 else 0
            yaz("RSI:",round(rv,1))
        if mc:
            score+=1 if mc[2]>0 else -1
            yaz("MACD:", "pozitif" if mc[2]>0 else "negatif")
        if e20:score+=1 if price>e20[-1] else -1
        if e50:score+=1 if price>e50[-1] else -1
        yaz("Oynaklık:",round(vol,2),"% | maksimum düşüş:",round(dd,1),"% | risk:",level)
        yaz("Yorum:","Teknik görünüm olumluya yakın." if score>=2 else
            "Teknik görünüm zayıf." if score<=-2 else "Göstergeler karışık; temkinli izlenebilir.")
        yaz("Bu özellik canlı veriyi kurallarla yorumlar; üretken yapay zekâ değildir ve yatırım tavsiyesi vermez.")
    except Exception as e:yaz(h,"için yanıt oluşturulamadı:",e)


BG=(.015,.015,.02,1);CARD=(.085,.085,.095,1);ORANGE=(1,.42,.06,1);PURPLE=ORANGE;GREEN=(.12,.58,.34,1);RED=(.75,.22,.32,1);GREY=(.18,.18,.20,1);WHITE=(.97,.97,.97,1)
TIPS={"analiz":"BIST: THYAO ZOREN | ABD: US_NVDA | Favoriler: F","yz":"YZ analizi: THYAO veya US_NVDA","bilanco":"BIST hissesi: THYAO ZOREN","portfoy":"Her satıra: HISSE ADET ALIŞ_FİYATI","favori":"Hisse yaz, Ekle veya Sil'e dokun.","sohbet":"Örnek: THYAO bugün nasıl? | AKBNK riskli mi?","haber":"Haberlerini incelemek istediğin hisse kodunu yaz.","harita":"Seçili büyük BIST hisselerinin günlük değişimi."}
HINT={"analiz":"THYAO ZOREN US_NVDA","yz":"THYAO US_NVDA","bilanco":"THYAO ZOREN","portfoy":"THYAO 100 250\nUS_NVDA 3 120","favori":"THYAO ZOREN","sohbet":"THYAO bugün nasıl?","haber":"THYAO","harita":"BIST"}
class BorsaApp(App):
    def build(self):
        global FAV,LOG
        os.makedirs(self.user_data_dir,exist_ok=True);FAV=os.path.join(self.user_data_dir,"favoriler.txt");LOG=os.path.join(self.user_data_dir,"borsa_sonuc.txt")
        self.title="Piyasa Gözü";self.scale=1.;self.busy=False;self.sound_on=True;self.sounds={}
        Window.clearcolor=BG;Window.softinput_mode="below_target";self.make_sounds()
        root=BoxLayout(orientation="vertical",padding=6,spacing=5)
        with root.canvas.before:Color(*BG);self.bg=Rectangle(pos=root.pos,size=root.size)
        root.bind(pos=lambda o,v:setattr(self.bg,"pos",o.pos),size=lambda o,v:setattr(self.bg,"size",o.size))

        # Üst kontrol alanı sabit; ana ekran aşağı-yukarı kaydırılabilir.
        top=BoxLayout(size_hint_y=None,height=82,spacing=6)
        self.heading=Label(text="[b]PİYASA GÖZÜ[/b]",markup=True,color=ORANGE,font_size=24)
        top.add_widget(self.heading)
        self.sound=Button(text="Ses: AÇIK",size_hint_x=None,width=112,font_size=18,background_normal="",background_color=GREEN)
        self.sound.bind(on_press=lambda *_:self.toggle_sound());top.add_widget(self.sound)
        for txt,d in (("A−",-.1),("A+",.1)):
            b=Button(text=txt,size_hint_x=None,width=66,font_size=24,background_normal="",background_color=GREY)
            b.bind(on_press=lambda _,v=d:self.resize_text(v));top.add_widget(b)
        root.add_widget(top)

        self.scroll=ScrollView(do_scroll_x=False,do_scroll_y=True,bar_width=12,
                               scroll_type=["bars","content"],size_hint=(1,1))
        self.content=BoxLayout(orientation="vertical",padding=4,spacing=10,
                               size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter("height"))
        self.scroll.add_widget(self.content)
        root.add_widget(self.scroll)

        self.tabs={}
        for group in ((("Analiz","analiz"),("YZ Analiz","yz"),("Bilanço","bilanco"),("Portföy","portfoy")),
                      (("Favori","favori"),("Akıllı Sohbet","sohbet"),("Haber Analizi","haber"),("Isı Haritası","harita"))):
            row=BoxLayout(size_hint_y=None,height=92,spacing=6)
            for title,key in group:
                b=ToggleButton(text=title,group="tabs",background_normal="",background_down="",
                               background_color=GREY,color=WHITE,font_size=16)
                b.bind(on_press=lambda _,k=key:self.select(k));row.add_widget(b);self.tabs[key]=b
            self.content.add_widget(row)

        self.tip=Label(size_hint_y=None,height=58,color=(.8,.77,.94,1),halign="left",valign="middle")
        self.tip.bind(size=lambda o,v:setattr(o,"text_size",v));self.content.add_widget(self.tip)
        self.entry=TextInput(size_hint_y=None,height=150,multiline=True,background_normal="",
                             background_active="",background_color=CARD,foreground_color=WHITE,
                             cursor_color=WHITE,padding=14,font_size=21)
        self.content.add_widget(self.entry)
        self.buttons=BoxLayout(size_hint_y=None,height=112,spacing=8);self.content.add_widget(self.buttons)
        self.output=TextInput(readonly=True,size_hint_y=None,height=520,background_normal="",
                              background_active="",background_color=CARD,foreground_color=WHITE,
                              padding=14,font_size=19,scroll_x=0,scroll_y=1,
                              do_wrap=True)
        self.content.add_widget(self.output)
        self.content.add_widget(Label(text="Geçmiş verilere dayanır; yatırım tavsiyesi değildir.",
                                      size_hint_y=None,height=42,color=(.72,.7,.84,1),font_size=14))
        self.select("analiz");self.apply_sizes();self.show("Hazır. Hisse kodunu yazıp Çalıştır'a dokun.");return root
    def make_sounds(self):
        try:
            for name,notes in {"tik":[1100],"onay":[700,1000],"sil":[480]}.items():
                path=os.path.join(self.user_data_dir,"sound_"+name+".wav")
                if not os.path.exists(path):
                    rate=22050;frames=[]
                    for hz in notes:
                        n=int(rate*.085)
                        for i in range(n):
                            env=min(1,i/(rate*.004))*(1-i/n);v=math.sin(2*math.pi*hz*i/rate)*env*.42
                            frames.append(struct.pack("<h",int(v*32767)))
                    with wave.open(path,"wb") as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(b"".join(frames))
                s=SoundLoader.load(path)
                if s:self.sounds[name]=s
        except Exception as e:print("Ses hazırlanamadı:",e)
    def play(self,n="tik"):
        if self.sound_on:
            try:
                s=self.sounds.get(n)
                if s:s.stop();s.play()
            except:pass
    def toggle_sound(self):
        self.sound_on=not self.sound_on;self.sound.text="Ses: AÇIK" if self.sound_on else "Ses: KAPALI";self.sound.background_color=GREEN if self.sound_on else GREY
        if self.sound_on:self.play("onay")
    def resize_text(self,d):self.scale=max(.8,min(1.7,self.scale+d));self.apply_sizes();self.play()
    def apply_sizes(self):
        s=self.scale;self.heading.font_size=25*s;self.tip.font_size=17*s;self.entry.font_size=22*s;self.output.font_size=20*s
        for b in self.tabs.values():b.font_size=16*s
        for b in self.buttons.children:b.font_size=19*s
    def show(self,t):
        self.output.text=t
        # Sonuç kutusu sabit kalır; uzun metin kutunun içinde parmakla kaydırılır.
        self.output.height=520
        self.output.cursor=(0,0)
        self.output.scroll_y=1
    def select(self,k):
        self.mode=k
        for key,b in self.tabs.items():b.state="down" if key==k else "normal";b.background_color=ORANGE if key==k else GREY
        self.tip.text=TIPS[k];self.entry.hint_text=HINT[k];self.make_buttons()
        if k=="favori":self.list_favs()
    def make_buttons(self):
        self.buttons.clear_widgets()
        opts=[("Ekle",self.add_fav,GREEN),("Sil",self.del_fav,RED),("Liste",self.list_favs,GREY),("Analiz",self.fav_analysis,ORANGE),("YZ",self.fav_yz,ORANGE)] if self.mode=="favori" else [("Çalıştır",self.run_action,ORANGE),("Temizle",self.clear,GREY)]
        for name,fn,col in opts:
            b=Button(text=name,background_normal="",background_color=col,color=WHITE,font_size=23*self.scale);b.bind(on_press=lambda _,f=fn:(self.play("onay"),f()));self.buttons.add_widget(b)
    def clear(self):self.entry.text="";self.show("")
    def background(self,fn):
        if self.busy:return
        self.busy=True;self.show("İşlem yapılıyor, lütfen bekle...")
        def work():
            global OUT
            OUT=[]
            try:fn()
            except Exception as e:yaz("Hata:",e)
            result="\n".join(OUT);Clock.schedule_once(lambda dt:self.finish(result),0)
        threading.Thread(target=work,daemon=True).start()
    def finish(self,t):self.busy=False;self.show(t or "Sonuç bulunamadı.")
    def run_action(self):
        if self.mode=="portfoy":self.background(lambda:portfolio(self.entry.text));return
        if self.mode=="sohbet":self.background(lambda:akilli_sohbet(self.entry.text));return
        if self.mode=="haber":
            hs=self.entry.text.strip().upper().split()
            if not hs:self.show("Hisse kodu yaz.");return
            self.background(lambda:[haber_analiz(h) for h in hs]);return
        if self.mode=="harita":self.background(piyasa_haritasi);return
        hs=self.entry.text.strip().upper().split()
        if hs==["F"]:hs=favread()
        if not hs:self.show("Önce hisse kodu yaz.");return
        fn={"analiz":analiz,"yz":lambda a:[yz(h) for h in a],"bilanco":lambda a:[bilanco(h) for h in a]}[self.mode]
        self.background(lambda:fn(hs))
    def list_favs(self):
        a=favread();self.show("FAVORİLER:\n"+(" ".join(a) if a else "(boş)"))
    def add_fav(self):
        a=favread()
        for h in self.entry.text.upper().split():
            if h not in a:a.append(h)
        favwrite(a);self.entry.text="";self.list_favs()
    def del_fav(self):
        gone=self.entry.text.upper().split();favwrite([h for h in favread() if h not in gone]);self.entry.text="";self.list_favs()
    def fav_analysis(self):
        a=favread()
        if a:self.background(lambda:analiz(a))
        else:self.show("Favori listen boş.")
    def fav_yz(self):
        a=favread()
        if a:self.background(lambda:[yz(h) for h in a])
        else:self.show("Favori listen boş.")

if __name__=="__main__":BorsaApp().run()
