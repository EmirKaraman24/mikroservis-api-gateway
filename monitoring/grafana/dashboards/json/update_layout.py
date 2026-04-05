import json

def update_dashboard():
    with open('monitoring/grafana/dashboards/json/traffic_dashboard.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Toplam İstek (0,0, w:6, h:4)
    data["panels"][0]["gridPos"] = {"h": 4, "w": 6, "x": 0, "y": 0}

    # 2. Uptime (18,0, w:6, h:4) (we will move this to index 3 later, but let's just generate the list fresh)
    ds = {"uid": "prometheus", "type": "prometheus"}
    
    new_panels = []
    
    # --- ROW 1 ---
    new_panels.append({
      "datasource": ds, "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0}, "id": 10,
      "title": "Toplam API İstekleri", "type": "stat",
      "targets": [{"datasource": ds, "expr": "sum(flask_http_request_total)", "refId": "A"}],
      "options": {"colorMode": "value", "graphMode": "area", "textMode": "auto"}
    })
    new_panels.append({
      "datasource": ds, "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0}, "id": 11,
      "title": "Güvenlik Engellemeleri (401/403 vb.)", "type": "stat",
      "targets": [{"datasource": ds, "expr": "sum(flask_http_request_total{status=~\"4..\"})", "refId": "A"}],
      "options": {"colorMode": "value", "graphMode": "area", "textMode": "auto"}
    })
    new_panels.append({
      "datasource": ds, "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0}, "id": 12,
      "title": "Sunucu Hataları (500)", "type": "stat",
      "targets": [{"datasource": ds, "expr": "sum(flask_http_request_total{status=~\"5..\"})", "refId": "A"}],
      "options": {"colorMode": "background", "graphMode": "none", "textMode": "auto"}
    })
    new_panels.append({
      "datasource": ds, "gridPos": {"h": 4, "w": 6, "x": 18, "y": 0}, "id": 13,
      "title": "Sistem Uptime (Saniye)", "type": "stat",
      "targets": [{"datasource": ds, "expr": "time() - process_start_time_seconds{job=\"dispatcher\"}", "refId": "A"}],
      "options": {"colorMode": "value", "graphMode": "area", "textMode": "auto"}
    })
    
    # --- ROW 2 ---
    new_panels.append({
      "datasource": ds, "gridPos": {"h": 9, "w": 12, "x": 0, "y": 4}, "id": 14,
      "title": "Servis Trafik Yoğunluğu (İstek/Sn)", "type": "timeseries",
      "targets": [{"datasource": ds, "expr": "rate(flask_http_request_total[1m])", "legendFormat": "{{endpoint}} - {{status}}", "refId": "A"}],
      "options": {
        "legend": {"displayMode": "list", "placement": "bottom", "showLegend": True},
        "tooltip": {"mode": "single", "sort": "none"}
      }
    })
    new_panels.append({
      "datasource": ds, "gridPos": {"h": 9, "w": 6, "x": 12, "y": 4}, "id": 15,
      "title": "HTTP Yanıt (Status) Kodları", "type": "piechart",
      "targets": [{"datasource": ds, "expr": "sum by (status) (flask_http_request_total)", "legendFormat": "HTTP {{status}}", "refId": "A"}],
      "options": {
        "pieType": "donut",
        "legend": {"displayMode": "list", "placement": "bottom", "showLegend": True}
      }
    })
    new_panels.append({
      "datasource": ds, "gridPos": {"h": 9, "w": 6, "x": 18, "y": 4}, "id": 16,
      "title": "HTTP Metotları", "type": "piechart",
      "targets": [{"datasource": ds, "expr": "sum by (method) (flask_http_request_total)", "legendFormat": "{{method}} İstekleri", "refId": "A"}],
      "options": {
        "pieType": "donut",
        "legend": {"displayMode": "list", "placement": "bottom", "showLegend": True}
      }
    })
    
    # --- ROW 3 ---
    new_panels.append({
      "datasource": ds, "gridPos": {"h": 8, "w": 24, "x": 0, "y": 13}, "id": 17,
      "title": "Dispatcher Memory Kullanımı (MB)", "type": "timeseries",
      "targets": [{"datasource": ds, "expr": "process_resident_memory_bytes{job=\"dispatcher\"} / 1024 / 1024", "legendFormat": "RAM Kullanımı (MB)", "refId": "A"}],
      "options": {
        "legend": {"displayMode": "list", "placement": "bottom", "showLegend": True},
        "tooltip": {"mode": "single", "sort": "none"}
      }
    })
    
    data["panels"] = new_panels
    
    with open('monitoring/grafana/dashboards/json/traffic_dashboard.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

update_dashboard()
