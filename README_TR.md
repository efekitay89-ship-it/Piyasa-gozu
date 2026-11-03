# Piyasa Gözü – Android APK projesi

Bu klasör, çalışan Python/Kivy uygulamasını Android APK'ya derlemek için hazırlandı.

## APK oluşturma (GitHub Actions ile)
1. GitHub'da yeni, boş bir repository oluştur: `Piyasa-Gozu`.
2. Bu ZIP içindeki dosyaları repository'nin ana dizinine yükle.
3. GitHub'da **Actions** sekmesine gir.
4. `Piyasa Gozu APK` iş akışını seçip **Run workflow** düğmesine bas.
5. İşlem tamamlanınca çalışmanın altındaki **Artifacts** bölümünden `Piyasa-Gozu-APK` dosyasını indir.
6. ZIP içindeki APK'yı Android telefona gönderip kur. İlk kurulumda Android, bu kaynaktan uygulama yükleme izni isteyebilir.

## Önemli
- Bu ilk paket bir **debug APK**'dır. Test ve arkadaşlarla deneme için uygundur.
- Google Play'e yayımlamak için ayrıca imzalı release/AAB paketi, gizlilik politikası, mağaza görselleri ve Play Console hesabı gerekir.
- Bilanço özelliği `borsapy` paketini opsiyonel kullandığından ilk APK'da bilanço verisi gelmeyebilir. Diğer temel özellikler `requests` ve Kivy ile çalışır.
- Uygulama finansal veri için Yahoo Finance'e internet bağlantısı üzerinden erişir. Veriler gecikmeli/eksik olabilir; yatırım tavsiyesi değildir.
