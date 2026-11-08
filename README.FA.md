# بررسی OpenSERP؛ آیا Web UI دارد و دقیقاً چه کاری انجام می‌دهد؟

> **به‌روزرسانی:** فایل مستقل [`search.html`](./search.html) اکنون به مخزن اضافه شده و امکان جست‌وجوی چندموتوره، تفکیک ویدئو/متن و تحلیل JSON را با بازکردن مستقیم در مرورگر فراهم می‌کند. این رابط پنل مدیریت تنظیمات نیست و برای نمایش زمان و کیفیت قطعی ویدئو به دادهٔ ساختاریافته نیاز دارد. برای جست‌وجوی زنده، OpenSERP باید روشن باشد.


نتیجهٔ تحقیق: نسخهٔ OpenSERP که در مخزن `masterteams/openserp` دارید، یک موتور جست‌وجوی Self-Hosted مبتنی بر API است؛ نه یک موتور جست‌وجوی کامل با صفحهٔ اصلی مشابه گوگل و نه یک نرم‌افزار با پنل مدیریت گرافیکی.

این پروژه یک رابط تحت وب به نام Swagger UI دارد که برای مشاهده و آزمایش API استفاده می‌شود، اما در نسخهٔ بررسی‌شده پنلی برای مدیریت تنظیمات، پروکسی‌ها، موتورهای جست‌وجو و کانتینرها وجود ندارد.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub+1



## ۱. کدام رابط‌های تحت وب را دارد؟

[Dependencies - FastAPI](https://images.openai.com/static-rsc-4/7gn5gYz93CT-xUQG27kbZPKYJPOpXwSW3eNmaWIz4-8IMLzhFptSludkDnSn4m40-c9HBMMv_cD9Yl-QeRO5haotZrfYBQIPVEELAGgNL6l492eBrjWi6rta6pWD9dUsiIJrlaMftMrTvSVBHh67LzNMuT_quaw8SE30j7QS6fU?purpose=inline)

Swagger UI — رابط موجود

`http://localhost:7000/docs`

نمایش APIها، پارامترها، مدل پاسخ‌ها و امکان ارسال درخواست آزمایشی با دکمهٔ `Try it out`. برای توسعه‌دهنده مناسب است، اما پنل تنظیمات نیست.

[SearchApi / Open WebUI](https://images.openai.com/static-rsc-4/5NCxUx_4EuJztYR90_3IMGKDLxnhI9DXVM6m2Fnk-Snzz07Zg_Zs82dmD9ENGkZxZo1oGHj0SFXX8kIUpAX--D6NeRdg85L6WRYQkDZZUYkHfs_O7377S_V9094oOxlnAEoDs2B_iq5TAXRWI3N1yK5_jGT5Mh8VuAXC6Chq86s?purpose=inline)

Open WebUI — رابط جداگانه

می‌توانید OpenSERP را به Open WebUI متصل کنید تا مدل‌های هوش مصنوعی از موتور جست‌وجوی شما استفاده کنند. این ابزار بخشی از خود OpenSERP نیست.

همچنین مسیرهای زیر در API وجود دارند:

| آدرس            | عملکرد                               |
| --------------- | ------------------------------------ |
| `/docs`         | مستندات تعاملی Swagger               |
| `/openapi.yaml` | مشخصات OpenAPI                       |
| `/health`       | بررسی سلامت سرویس                    |
| `/ready`        | وضعیت آمادگی                         |
| `/stats`        | آمار عملکرد و وضعیت برخی اجزای داخلی |
| `/mega/engines` | فهرست موتورهای جست‌وجو               |

این مسیرها در مستندات رسمی پروژه ثبت شده‌اند.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub+1



## ۲. OpenSERP دقیقاً برای چیست؟

فرض کنید می‌خواهید Claude Code، یک AI Agent یا برنامهٔ خودتان بتواند در اینترنت جست‌وجو کند و اطلاعات صفحات را به صورت ساختاریافته بخواند.

OpenSERP این کار را انجام می‌دهد:

AI Agent / Claude Code / برنامهٔ شما

ارسال عبارت جست‌وجو از طریق API یا MCP

OpenSERP

اجرای جست‌وجو و استخراج نتایج

Google

Bing

DuckDuckGo

Yandex

Baidu

Ecosia

خروجی ساختاریافته

JSON، Markdown، لینک‌ها، عنوان‌ها، توضیحات و رتبهٔ نتایج

برای مثال، به‌جای باز کردن دستی گوگل، برنامهٔ شما درخواست زیر را به OpenSERP می‌فرستد:

```
curl "http://localhost:7000/google/search?text=best+open+source+LLM&limit=5"
```

OpenSERP نتایج جست‌وجو را با اطلاعاتی مانند عنوان، آدرس، توضیحات و رتبه برمی‌گرداند. همچنین می‌تواند محتوای صفحات پیدا‌شده را برای استفادهٔ هوش مصنوعی به Markdown تبدیل کند.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://openserp.org\&sz=32)

OpenSERP Docs+1



## ۳. امکانات اصلی OpenSERP

| قابلیت                                   | وضعیت       |
| ---------------------------------------- | ----------- |
| جست‌وجوی وب در ۶ موتور                   | &#x20;دارد  |
| جست‌وجوی تصویر                           | &#x20;دارد  |
| جست‌وجوی هم‌زمان در چند موتور            | &#x20;دارد  |
| استخراج متن صفحات و تبدیل به Markdown    | &#x20;دارد  |
| اتصال از طریق MCP، REST API و SDK        | &#x20;دارد  |
| تنظیم پروکسی HTTP/SOCKS5                 | &#x20;دارد  |
| Cache، Retry و Circuit Breaker           | &#x20;دارد  |
| Swagger UI برای آزمایش API               | &#x20;دارد  |
| پنل مدیریت گرافیکی تنظیمات               | &#x20;ندارد |
| داشبورد آماده برای SEO و مدیریت پروژه‌ها | &#x20;ندارد |
| جست‌وجوی دستی با صفحه‌ای شبیه گوگل       | &#x20;ندارد |

[image](https://www.google.com/s2/favicons?domain=https://openserp.org\&sz=32)

OpenSERP Docs+2

## ۴. تنظیمات آن چگونه انجام می‌شود؟

در مخزن شما فایل اصلی تنظیمات `config.yaml` است که می‌توانید در آن پارامترهایی مثل تعداد پردازش‌های مرورگر، کش، محدودیت درخواست‌ها، پروکسی‌ها و موتورهای فعال را تغییر دهید.

مثلاً تنظیمات موجود شامل موارد زیر است:

```
server:
  host: 0.0.0.0
  port: 7000

app:
  max_processes: 6
  timeout: 15

cache:
  ttl_seconds: 120
  max_size: 1000
```

ترتیب اولویت تنظیمات نیز به این صورت است:

`CLI flags > OPENSERP_* environment > config.yaml > defaults`

در نصب Docker شما، فایل `config.yaml` به‌صورت Read-Only وارد کانتینر می‌شود. برای اعمال مطمئن تغییرات پیکربندی می‌توانید دوباره `./install.sh` را اجرا کنید تا کانتینر بازسازی یا بازایجاد شود.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://openserp.org\&sz=32)

OpenSERP Docs+1



## ۵. برای کار با Claude Code چقدر مناسب است؟

یکی از کاربردهای مهم آن همین است. مستندات رسمی روش اتصال را معرفی کرده‌اند:

```
claude mcp add openserp -- npx -y @openserp/mcp
```

این دستور یک MCP Server جداگانه را به Claude Code معرفی می‌کند. برای سروری که روی ماشین دیگری اجرا می‌شود باید آدرس OpenSERP را نیز با `OPENSERP_BASE_URL` تنظیم کنید.

پس Claude Code می‌تواند از ابزارهای جست‌وجو و استخراج محتوای وب استفاده کند، اما خود OpenSERP جایگزین مدیریت پروژه، حافظهٔ بلندمدت یا Knowledge Base نیست.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub+1



## ۶. برای داشتن Web UI واقعی چه راهی بهتر است؟

دو مسیر وجود دارد:

مسیر اول: اتصال به Open WebUI

اگر هدف شما جست‌وجوی اینترنت از محیط چت هوش مصنوعی است، می‌توانید OpenSERP را به Open WebUI متصل کنید. این اتصال در مستندات Open WebUI رسماً پشتیبانی شده است.

راهنما: [OpenSERP در Open WebUI](https://docs.openwebui.com/features/chat-conversations/web-search/providers/openserp/?utm_source=chatgpt.com)

مسیر دوم: اضافه کردن پنل اختصاصی به همین مخزن

اگر می‌خواهید خود OpenSERP را مدیریت کنید، پیشنهاد فنی من یک Web UI مستقل و سبک در کنار API موجود است؛ با امکاناتی مثل ویرایش امن تنظیمات، فعال/غیرفعال کردن موتورهای جست‌وجو، مدیریت پروکسی‌ها، تست جست‌وجو، آمار سرویس و مشاهدهٔ لاگ‌ها.

این مسیر نیازمند توسعهٔ جدید است. همچنین باید احراز هویت و محدودسازی دسترسی به پنل در طراحی لحاظ شود؛ چون OpenSERP اساساً یک API سرویس است.

## ۷. محدودیت مهم آن

OpenSERP صفحات نتایج موتورهای جست‌وجو را استخراج می‌کند و از API رسمی گوگل یا سایر موتورها استفاده نمی‌کند. به همین دلیل، CAPTCHA، محدودیت نرخ درخواست و مسدودسازی IP می‌توانند باعث شکست جست‌وجو شوند. حتی استفاده از Chromium و پروکسی هم موفقیت دائمی را تضمین نمی‌کند.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.openwebui.com\&sz=32)

docs.openwebui.com+1



جمع‌بندی: برای پروژهٔ شما، OpenSERP بیشتر یک زیرساخت جست‌وجوی اینترنت برای برنامه‌ها و AI Agentهاست. اگر هدف مدیریت خود سرویس از مرورگر است، افزودن یک پنل اختصاصی به مخزن `masterteams/openserp` مناسب‌تر از نصب Open WebUI است. اما اگر هدف چت با هوش مصنوعی همراه با جست‌وجوی وب باشد، Open WebUI بدون توسعهٔ پنل جدید کاربردی‌تر است.


برای جست‌وجو در تمام ۶ موتور جست‌وجوی OpenSERP به‌صورت هم‌زمان، باید از مسیر `/mega/search` با حالت `balanced` استفاده کنی.

اما یک محدودیت مهم وجود دارد: OpenSERP فعلاً فیلتر اختصاصی ویدئو برای کیفیت HD و مدت بیشتر از ۱۵ دقیقه ندارد. بنابراین می‌توانیم این شرایط را داخل عبارت جست‌وجو بنویسیم، ولی نتایج الزاماً همهٔ شرایط را رعایت نمی‌کنند.

### دستور پیشنهادی

```
curl -G "http://127.0.0.1:7000/mega/search" \
  --data-urlencode 'text=HD 1080p full video 20 minutes' \
  --data-urlencode 'engines=google,bing,yandex,baidu,duckduckgo,ecosia' \
  --data-urlencode 'mode=balanced' \
  --data-urlencode 'limit=20'
```

این دستور در همهٔ موتورهای فعال جست‌وجو می‌کند و نتایج صفحات وب مرتبط با ویدئو را برمی‌گرداند، نه یک فهرست تضمین‌شده از ویدئوهای HD بالای ۱۵ دقیقه.

### اگر از Swagger UI استفاده می‌کنی

وارد `http://127.0.0.1:7000/docs` شو، بخش `GET /mega/search` را باز کن و این مقادیر را وارد کن:

| پارامتر   | مقدار                                         |
| --------- | --------------------------------------------- |
| `text`    | `Python tutorial 1080p full video 20 minutes` |
| `engines` | `google,bing,yandex,baidu,duckduckgo,ecosia`  |
| `mode`    | `balanced`                                    |
| `limit`   | `20`                                          |
| `format`  | `json`                                        |

سپس `Execute` را بزن. به‌جای `Python tutorial` موضوع ویدئوی دلخواهت را بنویس. اگر فقط ویدئوهای یوتیوب را می‌خواهی، پارامتر `site` را برابر `youtube.com` بگذار.

نکته: در مستندات رسمی OpenSERP مسیر `/mega/video` یا پارامترهای `min_duration=900` و `quality=1080p` تعریف نشده‌اند. برای فیلتر واقعی مدت و کیفیت باید قابلیت جست‌وجوی تخصصی ویدئو به پروژه اضافه شود.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub+1
