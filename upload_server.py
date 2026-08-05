#!/usr/bin/env python3
"""Simple image upload UI for product detail page assets."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import cgi
import json
import urllib.parse

ROOT = Path(__file__).resolve().parent
IMAGES = ROOT / "images"
PORT = 8766

REQUIRED = [
    ("mainhead.jpg", "히어로 착용 컷"),
    ("vector.png", "구분선 아이콘"),
    ("valentine_bk1_3_4.jpg", "제품 클로즈업"),
    ("valentine_onoff.png", "스트랩 온오프"),
    ("valentine_style.jpg", "소파 스타일링"),
    ("valentine_details.jpg", "플랫레이 디테일"),
    ("value01_kipleather.jpg", "레더 소재"),
    ("value02_last.jpg", "시그니처 라스트"),
    ("value03_kipleather.jpg", "수제 공정"),
]


def status():
    return [
        {
            "name": name,
            "label": label,
            "exists": (IMAGES / name).is_file(),
            "size": (IMAGES / name).stat().st_size if (IMAGES / name).is_file() else 0,
        }
        for name, label in REQUIRED
    ]


HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>이미지 업로드 — YATO</title>
<style>
  :root {
    --bg: #f4f1ec;
    --card: #fff;
    --ink: #2a2420;
    --muted: #8a7e74;
    --line: #e4ddd4;
    --ok: #2f6b4f;
    --miss: #a85a3a;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: "Pretendard", "Apple SD Gothic Neo", sans-serif;
    background: linear-gradient(180deg, #f7f3ee 0%, #ebe4db 100%);
    color: var(--ink);
    min-height: 100vh;
  }
  .wrap { max-width: 920px; margin: 0 auto; padding: 40px 20px 80px; }
  h1 { font-size: 28px; font-weight: 600; margin: 0 0 8px; letter-spacing: -0.02em; }
  .sub { color: var(--muted); margin: 0 0 28px; line-height: 1.5; }
  .actions { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 24px; }
  .btn {
    display: inline-flex; align-items: center; gap: 8px;
    border: 1px solid var(--line); background: var(--card);
    color: var(--ink); text-decoration: none; padding: 10px 14px;
    border-radius: 10px; font-size: 14px; cursor: pointer;
  }
  .btn.primary { background: var(--ink); color: #fff; border-color: var(--ink); }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
  .card {
    background: var(--card); border: 1px solid var(--line); border-radius: 14px;
    padding: 14px; display: flex; flex-direction: column; gap: 10px;
  }
  .preview {
    aspect-ratio: 4/3; background: #f0ebe4; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    overflow: hidden; color: var(--muted); font-size: 13px; text-align: center;
  }
  .preview img { width: 100%; height: 100%; object-fit: cover; }
  .meta { display: flex; justify-content: space-between; gap: 8px; align-items: baseline; }
  .label { font-weight: 600; font-size: 14px; }
  .name { font-size: 12px; color: var(--muted); word-break: break-all; }
  .badge {
    font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 999px;
  }
  .badge.ok { background: #e7f3ec; color: var(--ok); }
  .badge.miss { background: #f8ebe6; color: var(--miss); }
  .drop {
    border: 1.5px dashed var(--line); border-radius: 10px; padding: 12px;
    text-align: center; color: var(--muted); font-size: 13px; cursor: pointer;
    transition: border-color .15s, background .15s;
  }
  .drop:hover, .drop.drag { border-color: var(--ink); background: #faf7f3; color: var(--ink); }
  input[type=file] { display: none; }
  .toast {
    position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
    background: var(--ink); color: #fff; padding: 10px 16px; border-radius: 999px;
    font-size: 13px; opacity: 0; pointer-events: none; transition: opacity .2s;
  }
  .toast.show { opacity: 1; }
</style>
</head>
<body>
  <div class="wrap">
    <h1>이미지 업로드</h1>
    <p class="sub">아래 슬롯에 파일을 드래그하거나 클릭해서 올리면 <code>images/</code> 폴더에 저장됩니다.<br>
    파일명은 자동으로 맞춰집니다. 업로드 후 미리보기 페이지를 새로고침하세요.</p>
    <div class="actions">
      <a class="btn primary" href="http://localhost:8765/index.html" target="_blank">상품 페이지 미리보기</a>
      <button class="btn" id="refresh">상태 새로고침</button>
    </div>
    <div class="grid" id="grid"></div>
  </div>
  <div class="toast" id="toast"></div>
<script>
async function load() {
  const res = await fetch('/api/status');
  const items = await res.json();
  const grid = document.getElementById('grid');
  grid.innerHTML = items.map(item => `
    <div class="card" data-name="${item.name}">
      <div class="preview" id="prev-${item.name}">
        ${item.exists
          ? `<img src="/images/${item.name}?t=${Date.now()}" alt="${item.label}">`
          : '아직 없음'}
      </div>
      <div class="meta">
        <div>
          <div class="label">${item.label}</div>
          <div class="name">${item.name}</div>
        </div>
        <span class="badge ${item.exists ? 'ok' : 'miss'}">${item.exists ? '완료' : '필요'}</span>
      </div>
      <label class="drop" data-name="${item.name}">
        클릭 또는 드래그해서 업로드
        <input type="file" accept="image/*" data-name="${item.name}">
      </label>
    </div>
  `).join('');

  grid.querySelectorAll('input[type=file]').forEach(input => {
    input.addEventListener('change', () => {
      if (input.files[0]) upload(input.dataset.name, input.files[0]);
    });
  });
  grid.querySelectorAll('.drop').forEach(drop => {
    drop.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('drag'); });
    drop.addEventListener('dragleave', () => drop.classList.remove('drag'));
    drop.addEventListener('drop', e => {
      e.preventDefault();
      drop.classList.remove('drag');
      const file = e.dataTransfer.files[0];
      if (file) upload(drop.dataset.name, file);
    });
  });
}

async function upload(name, file) {
  const fd = new FormData();
  fd.append('name', name);
  fd.append('file', file);
  const res = await fetch('/api/upload', { method: 'POST', body: fd });
  const data = await res.json();
  toast(data.ok ? `${name} 업로드 완료` : (data.error || '실패'));
  await load();
}

function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 1800);
}

document.getElementById('refresh').addEventListener('click', load);
load();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[{self.address_string()}] {fmt % args}")

    def _send(self, code, body, content_type="text/html; charset=utf-8"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/upload"):
            return self._send(200, HTML)

        if path == "/api/status":
            return self._send(200, json.dumps(status(), ensure_ascii=False), "application/json; charset=utf-8")

        if path.startswith("/images/"):
            name = Path(path).name
            file_path = IMAGES / name
            if not file_path.is_file():
                return self._send(404, "Not found", "text/plain")
            ctype = "image/png" if name.lower().endswith(".png") else "image/jpeg"
            return self._send(200, file_path.read_bytes(), ctype)

        return self._send(404, "Not found", "text/plain")

    def do_POST(self):
        if self.path != "/api/upload":
            return self._send(404, json.dumps({"ok": False, "error": "not found"}), "application/json")

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("Content-Type", ""),
            },
        )
        name = form.getvalue("name")
        file_item = form["file"] if "file" in form else None
        allowed = {n for n, _ in REQUIRED}

        if name not in allowed or file_item is None or not getattr(file_item, "file", None):
            return self._send(400, json.dumps({"ok": False, "error": "invalid upload"}), "application/json")

        IMAGES.mkdir(exist_ok=True)
        dest = IMAGES / name
        dest.write_bytes(file_item.file.read())
        return self._send(200, json.dumps({"ok": True, "name": name}), "application/json")


if __name__ == "__main__":
    IMAGES.mkdir(exist_ok=True)
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Upload UI: http://127.0.0.1:{PORT}/")
    server.serve_forever()
