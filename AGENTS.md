# Turkish Finance Synthetic Data Pipeline — Ajan Sözleşmesi

## Amaç

Küçük, denetlenebilir ve yeniden üretilebilir bir Türkçe finans araç kullanımı veri üretim hattını koru. Doğru araç seçimi kadar araç çağırmama, netleştirme, hata kurtarma, kaynak güvenilirliği ve finansal güvenlik davranışlarını da koru.

## Başlangıç

1. `README.md` ve `config.yaml` dosyalarını oku.
2. Her kayıt veya davranış değişikliğinden önce `.agents/skills/behavior-taxonomy/SKILL.md` dosyasını oku.
3. `uv run python automation/harness.py status` çalıştır.
4. İşe uygun diğer `.agents/skills/*/SKILL.md` dosyasını oku.
5. Değişiklikten sonra `uv run python automation/harness.py validate` çalıştır.

## Değişmezler

- Eğitim çıktısı yalnızca `id`, `messages` ve `tools` alanlarını içerir.
- Kayıtta sunulmayan bir araç çağrılamaz.
- Araç ve parametre kimlikleri çevrilemez.
- Güncel piyasa verisi, banka koşulları, vergi ve mevzuat araç gerektirir.
- Belirsiz tarih veya maddi parametre tahmin edilemez; kullanıcıdan netleştirme istenir.
- Yan etkili finansal işlemler açık kullanıcı onayı ve çalışma zamanı yetkisi gerektirir.
- Araç hatası veya eski sonuç başarılı ve güncel veri gibi sunulamaz.
- Bölme ataması `group_id` düzeyinde yapılır.
- Otomatik `valid` durumu insan incelemesinden geçmiş `accepted` durumu değildir.
- Zincirleme düşünce, inceleme notu ve iç üst veri eğitim satırına yazılamaz.

## Değişiklik yöntemi

- Yeni davranış ekleme; mevcut 16 davranıştan en yakın olanı seç.
- Yeni araç şeması için `tool-schema-onboarding` becerisini uygula.
- Yeni kayıt veya kaynak için `dataset-curation` becerisini uygula.
- İşlem, kimlik bilgisi veya finansal risk içeren kayıt için `financial-safety-review` becerisini uygula.
- Dışa aktarma değişikliği için `dataset-release` becerisini uygula.
- Kaynak, üretici, doğrulayıcı, test ve belgeyi aynı değişiklikte güncelle.
- Geçici uyumluluk katmanı veya eski ad takma adı bırakma.

## Kapanış kontrolleri

```bash
uv run python automation/harness.py validate
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python automation/repair_mojibake.py --check
```
