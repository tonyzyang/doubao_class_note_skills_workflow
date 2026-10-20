#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""由 content.json 构建「课堂同步 + 全讲复习」单个离线 HTML。

用法：
    python build_html.py content.json --out "课程·完整讲义.html" [--echarts path]
特性：幻灯片图 base64 内嵌、ECharts 内联、无外链；唯一的“画”是思维导图。
content.json 结构见 assets/content_template.json。缺失某一节自动跳过。
"""
import argparse
import base64
import html
import json
import os
import urllib.parse

E = html.escape


def render_blocks(blocks):
    out = []
    for b in blocks:
        t = b.get("type", "p")
        if t == "p":
            out.append("<p>%s</p>" % E(b["text"]))
        elif t == "ul":
            out.append("<ul>" + "".join("<li>%s</li>" % E(x) for x in b["items"]) + "</ul>")
        elif t == "note":
            out.append('<div class="note"><span class="note-tag">本页要点</span>%s</div>' % E(b["text"]))
        elif t == "ex":
            out.append('<div class="ex"><span class="ex-tag">课上举例</span>%s</div>' % E(b["text"]))
    return "\n".join(out)


def sec_head(title, desc, top=None):
    style = (' style="margin-top:%dpx"' % top) if top else ""
    return '<div class="sec-head"%s><h2>%s</h2><p>%s</p></div>' % (style, E(title), E(desc))


def fmt_time(sec):
    sec = int(round(sec))
    m, s = divmod(sec, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)
    return "%d:%02d" % (m, s)


def clip_html(cid, anchor, title, a):
    """渲染一个音频片段条：播放按钮 + 起止时间/时长 + 片段内进度条。"""
    is_pass = a.get("pass")
    cls = "clip pass" if is_pass else "clip"
    label = "一带而过" if is_pass else "本片段录音"
    return (
        '<div class="%s" data-clip="%s" data-anchor="%s" data-title="%s" '
        'data-start="%s" data-end="%s">\n'
        '  <button class="clip-btn" type="button" aria-label="播放本片段">'
        '<span class="ic-play"></span><span class="ic-pause"></span></button>\n'
        '  <div class="clip-body">\n'
        '    <div class="clip-meta"><span class="clip-label">%s</span>'
        '<span class="clip-time tnum">%s – %s · 时长 %s</span></div>\n'
        '    <div class="clip-track"><div class="clip-fill"></div></div>\n'
        '  </div>\n</div>'
        % (cls, cid, anchor, E(title), a["start"], a["end"], label,
           fmt_time(a["start"]), fmt_time(a["end"]), fmt_time(a["dur"])))


def build(data, base, echarts_path):
    def image_data(path):
        p = os.path.join(base, path)
        with open(p, "rb") as f:
            raw = f.read()
        mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
        return "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode())

    parts = data.get("parts", [])
    rev = data.get("review", {})

    # ---------- 导航 ----------
    nav = []
    if data.get("opening"):
        nav.append('<a href="#opening">课程背景</a>')
    for i, part in enumerate(parts, 1):
        nav.append('<a href="#part%d">%s</a>' % (i, E(part.get("name", "第%d部分" % i))))
    if data.get("qa"):
        nav.append('<a href="#qa">现场问答</a>')
    if rev:
        nav.append('<a href="#review">全讲复习</a>')
    nav_html = "\n  ".join(nav)

    # ---------- 开场 ----------
    opening_html = ""
    if data.get("opening"):
        cards = "\n".join(
            '<div class="open-card"><h4>%s</h4><p>%s</p></div>'
            % (E(x["heading"]), E(x["body"])) for x in data["opening"])
        opening_clip = ""
        if data.get("opening_audio"):
            opening_clip = "\n" + clip_html("clip-opening", "opening", "开场", data["opening_audio"])
        opening_html = (
            '<section id="opening">\n'
            + sec_head("开场：课程背景", "正式进入内容前，先交代课程的由来与改革的全貌")
            + '\n<div class="grid">\n%s\n</div>%s\n</section>' % (cards, opening_clip))

    # ---------- 幻灯片 ----------
    slide_count = 0
    parts_html = []
    for i, part in enumerate(parts, 1):
        rows = []
        for s in part.get("slides", []):
            raw_title = s["title"]
            title = E(raw_title)
            if s.get("image"):
                slide_count += 1
                num = s.get("number") or slide_count
                raw_anchor = s.get("anchor", "s%d" % num)
                anchor = E(raw_anchor)
                clip = ""
                if s.get("audio"):
                    clip = "\n" + clip_html("clip-%s" % raw_anchor, raw_anchor, raw_title, s["audio"])
                rows.append(
                    '<article class="slide" id="%s">\n'
                    '  <div class="slide-head"><span class="num">%02d</span><h3>%s</h3></div>\n'
                    '  <figure><img alt="%s" src="%s"></figure>\n'
                    '  <div class="talk">%s</div>%s\n</article>'
                    % (anchor, num, title, title, image_data(s["image"]),
                       render_blocks(s.get("blocks", [])), clip))
            else:
                tag = E(s.get("tag", "补讲"))
                raw_anchor = s.get("anchor", "text%d" % i)
                anchor = E(raw_anchor)
                clip = ""
                if s.get("audio"):
                    clip = "\n" + clip_html("clip-%s" % raw_anchor, raw_anchor, raw_title, s["audio"])
                rows.append(
                    '<article class="slide text-slide" id="%s">\n'
                    '  <div class="slide-head"><span class="num text-num">%s</span><h3>%s</h3></div>\n'
                    '  <div class="talk">%s</div>%s\n</article>'
                    % (anchor, tag, title, render_blocks(s.get("blocks", [])), clip))
        parts_html.append(
            '<section id="part%d">\n%s\n%s\n</section>'
            % (i, sec_head(part.get("name", "第%d部分" % i), part.get("desc", "")),
               "\n".join(rows)))
    parts_html = "\n".join(parts_html)

    # ---------- 现场问答 ----------
    qa_html = ""
    if data.get("qa"):
        rows = []
        for i, x in enumerate(data["qa"], 1):
            rows.append(
                '<div class="qa">\n  <div class="q"><span class="qa-num">问 %d</span>%s</div>\n'
                '  <div class="a"><span class="qa-tag">答</span>%s</div>\n</div>'
                % (i, E(x["q"]), E(x["a"])))
        qa_clip = ""
        if data.get("qa_audio"):
            qa_clip = clip_html("clip-qa", "qa", "现场问答", data["qa_audio"])
        qa_html = ('<section id="qa">\n'
                   + sec_head("现场问答", "课程结束前，同学提问，逐一作答")
                   + "\n" + "\n".join(rows) + "\n" + qa_clip + "\n</section>")

    # ---------- 复习 ----------
    rmap = rev.get("map")
    paths = rev.get("paths", [])
    conclusions = rev.get("conclusions", [])
    quiz = rev.get("quiz", [])
    timeline = rev.get("timeline", [])
    modules = rev.get("modules", [])
    numbers = rev.get("numbers", [])
    confuse = rev.get("confuse", [])
    talks = rev.get("talks", [])
    transfer = rev.get("transfer", [])

    rb = []
    if rmap:
        rb.append(
            '<div class="chart-card">\n    <div class="chart-title">知识地图 · 思维导图</div>\n'
            '    <div id="chart-map"></div>\n'
            '    <div class="chart-note">默认展示一级分支，点击圆点展开下属知识点，可拖拽平移、滚轮缩放。</div>\n  </div>')
    if paths:
        cards = []
        for x in paths:
            lis = "".join("<li>%s</li>" % E(i) for i in x["items"])
            cards.append('<div class="path-card"><div class="path-time">%s</div><div class="path-name">%s</div><ul>%s</ul></div>'
                         % (E(x["time"]), E(x["name"]), lis))
        rb.append(sec_head("复习路径", "按可支配时间选择对应的复习节奏", 30))
        rb.append('<div class="path-grid">\n' + "\n".join(cards) + "\n</div>")
    if conclusions:
        rb.append(sec_head("核心结论（先记住这 %d 条）" % len(conclusions), "密集细节之前先建立骨架"))
        rb.append('<div class="concl">' + "".join(
            '<div class="concl-item"><p>%s</p></div>' % E(c) for c in conclusions) + "</div>")
    if quiz:
        det = []
        for x in quiz:
            lis = "".join("<li>%s</li>" % E(a) for a in x["answer"])
            det.append('<details><summary>%s</summary><div class="ans"><ul>%s</ul></div></details>'
                       % (E(x["q"]), lis))
        rb.append(sec_head("主动回忆自测（%d 题）" % len(quiz), "先自己开口作答，再展开核对要点"))
        rb.append('<div class="quiz">\n' + "\n".join(det) + "\n</div>")
    if timeline:
        rb.append(sec_head("时间脉络", "按时间顺序串起改革的关键节点"))
        rb.append('<ul class="tl-list">' + "".join(
            '<li><span class="tl-t">%s</span><span class="tl-d">%s</span></li>'
            % (E(x["time"]), E(x["text"])) for x in timeline) + "</ul>")
    if modules:
        rb.append(sec_head("核心模块（高度浓缩）", "每个模块一句话把握本质"))
        rb.append('<div class="mod-list">' + "".join(
            '<div class="mod-row"><span class="mod-no">模块 %d</span><div><b>%s</b><p>%s</p></div></div>'
            % (i, E(x["name"]), E(x["essence"])) for i, x in enumerate(modules, 1)) + "</div>")
    if numbers:
        rb.append(sec_head("高频数字速记", "关键数字一览（多为口述约数，口径以正文为准）"))
        rb.append('<div class="numgrid">' + "".join(
            '<div class="numcard"><div class="v tnum">%s</div><div class="k">%s</div></div>'
            % (E(x["value"]), E(x["label"])) for x in numbers) + "</div>")
    if confuse:
        rb.append(sec_head("易混点与常见错误", "辨析容易混淆的概念"))
        rb.append('<ul class="confuse">' + "".join(
            '<li><b>%s：</b>%s</li>' % (E(x["term"]), E(x["note"])) for x in confuse) + "</ul>")
    if talks:
        rb.append(sec_head("面试 / 考试可表达的话术", "每段约 30–60 秒，可直接复述"))
        rb.append("\n".join('<div class="talkpt"><h4>%s</h4><p>%s</p></div>'
                            % (E(x["topic"]), E(x["script"])) for x in talks))
    if transfer:
        rb.append(sec_head("迁移清单", "把本讲框架迁移到新场景的具体动作"))
        rb.append("\n".join('<div class="move-item"><div class="idx">%d</div><div>%s</div></div>'
                            % (i, E(x)) for i, x in enumerate(transfer, 1)))
    review_html = ""
    if rb:
        review_html = ('<section id="review">\n'
                       + sec_head("全讲复习", "只做文字、列表与思维导图，不另画课程图表")
                       + "\n" + "\n".join(rb) + "\n</section>")

    # ---------- 结尾 ----------
    closing_html = ""
    if data.get("closing"):
        closing_html = ('<div class="closing">\n  <h2>本 讲 结 束</h2>\n  <p>%s</p>\n</div>'
                        % E(data["closing"]))

    # ---------- Hero 统计 ----------
    sp = []
    if slide_count:
        sp.append('<div><b>%d</b><span>页课堂幻灯片</span></div>' % slide_count)
    if conclusions:
        sp.append('<div><b>%d</b><span>条核心结论</span></div>' % len(conclusions))
    if quiz:
        sp.append('<div><b>%d</b><span>题自测（含现场问答）</span></div>' % len(quiz))
    if modules:
        sp.append('<div><b>%d</b><span>个核心模块</span></div>' % len(modules))
    stats_html = '<div class="stats">\n    ' + "\n    ".join(sp) + "\n  </div>"

    # ---------- favicon ----------
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
           "<rect width='100' height='100' rx='18' fill='#1f3a52'/>"
           "<text x='50' y='70' font-size='52' text-anchor='middle' fill='#ffe9c7' "
           "font-family='Georgia,serif'>%s</text></svg>" % data.get("favicon", "课"))
    favicon_html = '<link rel="icon" href="data:image/svg+xml,%s">' % urllib.parse.quote(svg, safe="")

    # ---------- 音频播放器（完整录音内嵌 + 底部控制条）----------
    audio_player_html = ""
    if data.get("audio"):
        apath = os.path.join(base, data["audio"]["src"])
        with open(apath, "rb") as f:
            ab64 = base64.b64encode(f.read()).decode()
        audio_player_html = (
            '<audio id="main-audio" preload="auto" '
            'src="data:audio/mpeg;base64,%s"></audio>\n'
            '<div class="nowbar" id="nowbar">\n'
            '  <div class="nowbar-inner">\n'
            '    <button class="nowbar-btn" id="nb-btn" type="button" aria-label="播放或暂停">'
            '<span class="nb-ic-play"></span><span class="nb-ic-pause"></span></button>\n'
            '    <a class="nowbar-title" id="nb-title" href="#opening">本片段</a>\n'
            '    <div class="nowbar-track" id="nb-track"><div class="nowbar-fill" id="nb-fill"></div></div>\n'
            '    <span class="nowbar-times tnum"><span id="nb-cur">0:00</span> / <span id="nb-dur">0:00</span></span>\n'
            '  </div>\n</div>') % ab64

    # ---------- 脚本 ----------
    echarts_js = open(echarts_path, encoding="utf-8").read().replace("</script>", "<\\/script>")
    map_js = ""
    if rmap:
        map_js = MAP_SCRIPT % json.dumps(rmap, ensure_ascii=False)
    clip_js = CLIP_SCRIPT if data.get("audio") else ""
    scripts_html = "<script>\n%s\n</script>\n%s\n%s" % (echarts_js, map_js, clip_js)

    doc = TEMPLATE % (
        favicon_html, E(data.get("title", "课堂讲义")), CSS,
        nav_html,
        E(data.get("title", "课堂讲义")),
        E(data.get("subtitle", "")),
        E(data.get("oneline", "")),
        stats_html,
        opening_html, parts_html, qa_html, review_html, closing_html,
        audio_player_html, scripts_html)
    return doc, slide_count, len(conclusions), len(quiz), len(modules)


MAP_SCRIPT = '''<script>
(function(){
  var mapData = %s;
  var FONT = '"PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif';
  var C = {indigo:"#2d4f6f", cinnabar:"#b3532b", gold:"#9c7a38", jade:"#3f6b5c", line:"#c6b99a", ink:"#22303c", soft:"#6a6457"};
  function init(){
    var el = document.getElementById("chart-map");
    if(!el || !window.echarts){
      if(el) el.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%%;color:#6a6457;font-size:13px;text-align:center">思维导图需要 ECharts，已内联，正常应可显示。</div>';
      return;
    }
    var c = echarts.init(el, null, {renderer:"canvas"});
    c.setOption({
      tooltip:{trigger:"item",triggerOn:"mousemove",textStyle:{fontFamily:FONT,fontSize:12}},
      series:[{
        type:"tree", data:[mapData],
        top:"2%%", left:"14%%", bottom:"2%%", right:"22%%",
        orient:"LR", edgeShape:"polyline", expandAndCollapse:true,
        initialTreeDepth:1, roam:true,
        symbol:"circle", symbolSize:8,
        lineStyle:{color:C.line,width:1.2},
        itemStyle:{color:C.indigo,borderColor:C.indigo},
        label:{position:"left",verticalAlign:"middle",align:"right",fontSize:13,color:C.ink,fontFamily:FONT,fontWeight:500},
        leaves:{label:{position:"right",verticalAlign:"middle",align:"left",color:"#4a4550",fontWeight:400,fontSize:12.5}},
        emphasis:{focus:"descendant"},
        levels:[
          {itemStyle:{color:C.cinnabar,borderColor:C.cinnabar,symbolSize:12},label:{fontSize:15,fontWeight:700,color:C.indigo}},
          {itemStyle:{color:C.gold,borderColor:C.gold,symbolSize:10},label:{fontSize:13.5,fontWeight:700,color:"#5f4a1f"},lineStyle:{width:1.4}},
          {itemStyle:{color:C.jade,borderColor:C.jade},lineStyle:{color:"#d8cfba"},label:{fontSize:12.5}}
        ],
        animationDuration:450, animationDurationUpdate:500
      }]
    });
    window.addEventListener("resize", function(){c.resize();});
  }
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
</script>'''


CLIP_SCRIPT = '''<script>
(function(){
  var audio = document.getElementById("main-audio");
  var clips = Array.prototype.slice.call(document.querySelectorAll("[data-clip]"));
  var nowbar = document.getElementById("nowbar");
  var nbBtn = document.getElementById("nb-btn");
  var nbTitle = document.getElementById("nb-title");
  var nbFill = document.getElementById("nb-fill");
  var nbCur = document.getElementById("nb-cur");
  var nbDur = document.getElementById("nb-dur");
  var nbTrack = document.getElementById("nb-track");
  var active = null;

  function fmt(sec){
    sec = Math.max(0, Math.round(sec));
    var m = Math.floor(sec/60), s = sec % 60;
    return m + ":" + (s < 10 ? "0" : "") + s;
  }
  function rangeOf(c){
    return {start: parseFloat(c.getAttribute("data-start")),
            end: parseFloat(c.getAttribute("data-end"))};
  }
  function resetFill(c){
    var f = c.querySelector(".clip-fill"); if(f) f.style.width = "0";
  }
  function clearActive(){
    if(active){ active.classList.remove("playing"); resetFill(active); }
    active = null;
    nowbar.classList.remove("show");
    document.body.classList.remove("has-nowbar");
    nbFill.style.width = "0";
    nbBtn.classList.remove("is-playing");
  }
  function setActive(c){
    if(active && active !== c){ active.classList.remove("playing"); resetFill(active); }
    active = c;
    c.classList.add("playing");
    nbTitle.textContent = c.getAttribute("data-title") || "本片段";
    nbTitle.setAttribute("href", "#" + c.getAttribute("data-anchor"));
    var r = rangeOf(c);
    nbDur.textContent = fmt(r.end - r.start);
    nbCur.textContent = "0:00";
    nbFill.style.width = "0";
    nowbar.classList.add("show");
    document.body.classList.add("has-nowbar");
  }
  function playClip(c){
    if(active === c){ audio.pause(); return; }
    var r = rangeOf(c);
    audio.currentTime = r.start;
    setActive(c);
    var pr = audio.play();
    if(pr && pr.catch) pr.catch(function(){ /* 由用户点击触发，应可正常播放 */ });
  }
  clips.forEach(function(c){
    c.querySelector(".clip-btn").addEventListener("click", function(e){
      e.stopPropagation(); playClip(c);
    });
  });
  nbBtn.addEventListener("click", function(){
    if(!active) return;
    if(audio.paused){ audio.play(); } else { audio.pause(); }
  });
  audio.addEventListener("play", function(){
    if(active){ active.classList.add("playing"); nbBtn.classList.add("is-playing"); }
  });
  audio.addEventListener("pause", function(){
    nbBtn.classList.remove("is-playing");
  });
  audio.addEventListener("timeupdate", function(){
    if(!active) return;
    var r = rangeOf(active);
    var t = audio.currentTime;
    if(t >= r.end){
      audio.pause();
      clearActive();
      return;
    }
    var ratio = (t - r.start) / (r.end - r.start);
    ratio = Math.max(0, Math.min(1, ratio));
    var f = active.querySelector(".clip-fill");
    if(f) f.style.width = (ratio * 100) + "%";
    nbFill.style.width = (ratio * 100) + "%";
    nbCur.textContent = fmt(t - r.start);
  });
  audio.addEventListener("ended", clearActive);
  nbTrack.addEventListener("click", function(e){
    if(!active) return;
    var rect = nbTrack.getBoundingClientRect();
    var ratio = (e.clientX - rect.left) / rect.width;
    ratio = Math.max(0, Math.min(1, ratio));
    var r = rangeOf(active);
    audio.currentTime = r.start + ratio * (r.end - r.start);
  });
})();
</script>'''


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
%s
<title>%s</title>
<style>%s</style>
</head>
<body>
<nav class="topnav"><div class="wrap">
  <span class="brand">课堂同步讲义</span>
  %s
</div></nav>

<header class="hero"><div class="wrap">
  <h1>%s</h1>
  <p class="sub">%s</p>
  <p class="oneline">%s</p>
  %s
</div></header>

<main class="wrap">
%s
%s
%s
%s
%s
</main>

%s
%s
</body>
</html>
"""

CSS = """
:root{
  --ink:#22303c; --navy:#1f3a52; --navy2:#2d4f6f; --sand:#f4efe4; --card:#fcfaf4;
  --cinnabar:#b3532b; --pine:#3f6b5c; --gold:#9c7a38; --line:#e2d9c7; --muted:#6a6457;
}
*{box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{margin:0; background:var(--sand); color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC","Source Han Sans SC",sans-serif;
  font-size:16px; line-height:1.85; -webkit-text-size-adjust:100%;}
.wrap{max-width:980px; margin:0 auto; padding:0 20px;}
a{color:var(--navy2);}
.tnum{font-variant-numeric:tabular-nums;}
.topnav{position:sticky; top:0; z-index:50; background:rgba(31,58,82,.96); backdrop-filter:blur(4px);}
.topnav .wrap{display:flex; gap:6px; align-items:center; overflow-x:auto; padding-top:8px; padding-bottom:8px;}
.topnav .brand{color:#f0e6d2; font-weight:700; white-space:nowrap; margin-right:8px; letter-spacing:.5px;}
.topnav a{color:#e8e2d2; text-decoration:none; font-size:14px; padding:5px 12px; border-radius:999px; white-space:nowrap;}
.topnav a:hover{background:rgba(255,255,255,.14);}
.hero{background:linear-gradient(160deg,#1f3a52 0%,#274b6b 55%,#33597a 100%); color:#f6f0e2; padding:64px 0 54px;}
.hero h1{font-size:38px; line-height:1.3; margin:0 0 10px; font-family:Georgia,"Songti SC","STSong",serif; letter-spacing:1px;}
.hero .sub{font-size:19px; margin:0 0 18px; color:#e7dcc4;}
.hero .oneline{max-width:720px; font-size:15.5px; color:#d9e0e6; margin:0 0 30px;}
.stats{display:flex; flex-wrap:wrap; gap:14px;}
.stats div{background:rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.18); border-radius:12px; padding:14px 22px; min-width:120px;}
.stats b{display:block; font-size:26px; color:#ffe9c7; font-family:Georgia,serif;}
.stats span{font-size:13px; color:#d7dde3;}
section{padding:46px 0 10px;}
.sec-head{border-left:6px solid var(--cinnabar); padding:4px 0 4px 16px; margin-bottom:8px;}
.sec-head h2{margin:0; font-size:27px; color:var(--navy); font-family:Georgia,"Songti SC",serif;}
.sec-head p{margin:6px 0 0; color:var(--muted); font-size:15px;}
#opening .grid{display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:18px;}
.open-card{background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px 18px;}
.open-card h4{margin:0 0 6px; font-size:16px; color:var(--cinnabar);}
.open-card p{margin:0; font-size:15px; color:#3c424b;}
.slide{background:var(--card); border:1px solid var(--line); border-radius:16px; padding:22px 22px 24px; margin:26px 0; box-shadow:0 2px 10px rgba(80,60,30,.05);}
.slide-head{display:flex; align-items:baseline; gap:14px; margin-bottom:14px; border-bottom:1px dashed var(--line); padding-bottom:12px;}
.slide-head .num{font-family:Georgia,serif; font-size:26px; font-weight:700; color:var(--cinnabar); min-width:44px;}
.slide-head h3{margin:0; font-size:19px; color:var(--navy); line-height:1.5;}
figure{margin:0 0 16px; aspect-ratio:4/3;}
figure img{display:block; width:100%; height:100%; border-radius:10px; border:1px solid #d8d0bf; background:#f5f1e8; object-fit:contain;}
.text-slide{border:1px dashed #cdb985; background:#f8f5ec;}
.text-slide .slide-head{border-bottom-color:#e2d8c2;}
.text-num{color:var(--gold)!important; font-size:18px!important; min-width:54px!important;}
.missing-tip{margin:0 0 16px; background:#f2ead7; border:1px dashed #cdb985; border-radius:8px; padding:9px 14px; font-size:13.5px; color:#7a6534;}
.talk p{margin:0 0 13px;}
.talk ul{margin:4px 0 14px; padding-left:4px; list-style:none;}
.talk li{position:relative; padding-left:22px; margin:0 0 9px;}
.talk li::before{content:""; position:absolute; left:3px; top:12px; width:8px; height:8px; border-radius:2px; background:var(--pine);}
.note{margin:14px 0 6px; background:#f3f0e6; border:1px solid #e0d8c4; border-left:5px solid var(--pine); border-radius:8px; padding:12px 16px; font-size:15px; color:#3a444d;}
.note-tag{display:inline-block; background:var(--pine); color:#fff; font-size:12px; border-radius:5px; padding:1px 9px; margin-right:10px; vertical-align:1px;}
.ex{margin:14px 0; background:#faf3e6; border:1px solid #e8d9b8; border-left:5px solid var(--gold); border-radius:8px; padding:12px 16px; font-size:15px; color:#4a3f28;}
.ex-tag{display:inline-block; background:var(--gold); color:#fff; font-size:12px; border-radius:5px; padding:1px 9px; margin-right:10px; vertical-align:1px;}
.qa{background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px 18px; margin:16px 0;}
.qa .q{font-size:16px; color:var(--navy); font-weight:600; margin-bottom:10px; line-height:1.7;}
.qa .a{font-size:15px; color:#3a444d; line-height:1.85;}
.qa-num{display:inline-block; background:var(--cinnabar); color:#fff; font-size:12px; border-radius:5px; padding:1px 9px; margin-right:10px; font-weight:400; vertical-align:1px;}
.qa-tag{display:inline-block; background:var(--pine); color:#fff; font-size:12px; border-radius:5px; padding:1px 9px; margin-right:10px; vertical-align:1px;}
.chart-card{background:var(--card); border:1px solid var(--line); border-radius:12px; padding:20px 20px 12px; margin:18px 0;}
.chart-title{font-weight:700; color:var(--navy); font-size:16px; margin-bottom:2px;}
.chart-note{font-size:12.5px; color:var(--muted); margin-top:6px;}
#chart-map{width:100%; height:620px;}
.path-grid{display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-top:18px;}
.path-card{background:var(--card); border:1px solid var(--line); border-radius:12px; padding:18px; border-top:4px solid var(--navy);}
.path-card:nth-child(2){border-top-color:var(--pine);}
.path-card:nth-child(3){border-top-color:var(--gold);}
.path-card:nth-child(4){border-top-color:var(--cinnabar);}
.path-time{font-family:Georgia,serif; font-size:20px; font-weight:700; color:var(--navy);}
.path-name{font-size:13px; color:var(--muted); margin:2px 0 10px; letter-spacing:.05em;}
.path-card ul{list-style:none; font-size:13.5px; color:#3c424b; margin:0; padding:0;}
.path-card li{position:relative; padding-left:16px; margin:7px 0; line-height:1.7;}
.path-card li::before{content:""; position:absolute; left:0; top:10px; width:6px; height:6px; background:var(--gold); border-radius:1px;}
.concl{display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:18px; counter-reset:ci;}
.concl-item{counter-increment:ci; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px 18px 16px 16px;}
.concl-item p{margin:0; font-size:14.5px; position:relative; padding-left:46px;}
.concl-item p::before{content:counter(ci,decimal-leading-zero); position:absolute; left:0; top:1px; font-family:Georgia,serif; font-size:20px; font-weight:700; color:var(--cinnabar); border-right:2px solid var(--line); padding-right:12px; line-height:1.4;}
.quiz details{background:var(--card); border:1px solid var(--line); border-radius:12px; margin:10px 0; overflow:hidden;}
.quiz summary{cursor:pointer; padding:15px 18px; font-weight:600; font-size:15px; list-style:none; color:var(--navy); display:flex; align-items:flex-start; gap:12px;}
.quiz summary::-webkit-details-marker{display:none;}
.quiz details:not([open]) > *:not(summary){display:none;}
.quiz summary::before{content:"Q"; flex:none; font-family:Georgia,serif; font-weight:700; font-size:12px; color:#fff; background:var(--navy); width:22px; height:22px; border-radius:6px; display:flex; align-items:center; justify-content:center; margin-top:3px;}
.quiz summary::after{content:"＋"; margin-left:auto; color:var(--muted); font-size:18px; flex:none;}
.quiz details[open] summary::after{transform:rotate(45deg);}
.quiz .ans{padding:12px 18px 16px 52px; font-size:14px; color:#3c424b; border-top:1px dashed var(--line);}
.quiz .ans ul{margin:0; padding-left:20px;}
.quiz .ans li{margin:6px 0;}
.tl-list{list-style:none; margin:18px 0; padding:0;}
.tl-list li{display:flex; gap:16px; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:13px 18px; margin:10px 0; align-items:flex-start;}
.tl-t{flex:none; font-family:Georgia,serif; font-weight:700; color:var(--cinnabar); min-width:78px;}
.tl-d{font-size:14.5px; color:#3c424b;}
.mod-list{display:grid; grid-template-columns:1fr; gap:10px; margin-top:18px;}
.mod-row{display:flex; gap:14px; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:13px 18px; align-items:flex-start;}
.mod-no{flex:none; font-size:12px; letter-spacing:.1em; color:#fff; background:var(--navy); border-radius:6px; padding:3px 10px; margin-top:2px; white-space:nowrap;}
.mod-row b{color:var(--navy); font-size:15px;}
.mod-row p{margin:3px 0 0; font-size:14px; color:#3c424b;}
.numgrid{display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-top:18px;}
.numcard{background:#fffdf6; border:1px solid var(--line); border-radius:12px; padding:15px; text-align:center; min-width:0;}
.numcard .v{font-family:Georgia,serif; font-size:22px; font-weight:700; color:var(--cinnabar); line-height:1.2; overflow-wrap:break-word; word-break:break-word;}
.numcard .k{font-size:12px; color:var(--muted); margin-top:5px; line-height:1.5;}
.confuse{list-style:none; margin:18px 0; padding:0; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:18px 22px;}
.confuse li{position:relative; padding-left:20px; margin:11px 0; font-size:14.5px;}
.confuse li::before{content:""; position:absolute; left:0; top:12px; width:8px; height:8px; border-radius:2px; background:var(--gold);}
.confuse b{color:var(--cinnabar);}
.talkpt{border-left:4px solid var(--gold); background:rgba(156,122,56,.09); padding:14px 20px; border-radius:0 12px 12px 0; margin:14px 0;}
.talkpt h4{margin:0 0 6px; color:var(--gold); font-size:15px;}
.talkpt p{margin:0; font-size:14.5px; color:#3c424b;}
.move-item{display:flex; gap:14px; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 18px; margin:10px 0; font-size:14.5px;}
.move-item .idx{font-family:Georgia,serif; font-size:18px; color:var(--pine); font-weight:700; flex:none;}
.closing{margin:44px 0 60px; background:var(--card); border:1px solid var(--line); border-radius:16px; padding:32px 24px; text-align:center;}
.closing h2{margin:0 0 10px; color:var(--navy); font-family:Georgia,"Songti SC",serif;}
.closing p{margin:0 auto; max-width:700px; color:#3c424b; font-size:15px;}
/* 音频片段条 */
.clip{display:flex; align-items:center; gap:12px; margin-top:18px; background:#f0ece1; border:1px solid #e2d9c7; border-radius:10px; padding:9px 14px; transition:border-color .2s,background .2s,box-shadow .2s;}
.clip:hover{border-color:#cdb985;}
.clip.playing{border-color:var(--cinnabar); background:#f8ede2; box-shadow:0 2px 10px rgba(179,83,43,.12);}
.clip.pass{background:#ece8dd; border-color:#ded7c8; opacity:.92;}
.clip.pass .clip-label{color:var(--muted); font-weight:600;}
.clip.pass.playing{border-color:var(--gold); background:#f4ecdd; box-shadow:0 2px 10px rgba(156,122,56,.12);}
.clip.pass.playing .clip-btn{background:var(--gold);}
.clip-btn{flex:none; width:38px; height:38px; border-radius:50%; border:none; background:var(--navy); cursor:pointer; display:flex; align-items:center; justify-content:center; transition:background .2s;}
.clip-btn:hover{background:var(--navy2);}
.clip.playing .clip-btn{background:var(--cinnabar);}
.ic-play{display:block; width:0; height:0; border:7px solid transparent; border-left:12px solid #fff; margin-left:3px;}
.ic-pause{display:none; width:13px; height:15px; background:linear-gradient(to right,#fff 0,#fff 4px,transparent 4px,transparent 9px,#fff 9px,#fff 13px);}
.clip.playing .ic-play{display:none;}
.clip.playing .ic-pause{display:block;}
.clip-body{flex:1; min-width:0;}
.clip-meta{display:flex; justify-content:space-between; align-items:baseline; gap:10px; flex-wrap:wrap;}
.clip-label{font-size:13px; color:var(--cinnabar); font-weight:600;}
.clip-time{font-size:12.5px; color:var(--muted);}
.clip-track{height:4px; background:#e2dac7; border-radius:2px; margin-top:7px; overflow:hidden;}
.clip-fill{height:100%; width:0; background:linear-gradient(90deg,var(--cinnabar),var(--gold)); border-radius:2px;}
/* 底部固定控制条 */
body.has-nowbar{padding-bottom:66px;}
.nowbar{position:fixed; left:0; right:0; bottom:0; z-index:60; background:rgba(31,58,82,.97); display:none; box-shadow:0 -4px 18px rgba(0,0,0,.22);}
.nowbar.show{display:block;}
.nowbar-inner{max-width:980px; margin:0 auto; padding:9px 20px; display:flex; align-items:center; gap:14px;}
.nowbar-btn{flex:none; width:36px; height:36px; border-radius:50%; border:none; background:#ffe9c7; cursor:pointer; display:flex; align-items:center; justify-content:center;}
.nb-ic-play{display:block; width:0; height:0; border:6px solid transparent; border-left:10px solid var(--navy); margin-left:2px;}
.nb-ic-pause{display:none; width:11px; height:13px; background:linear-gradient(to right,var(--navy) 0,var(--navy) 3px,transparent 3px,transparent 8px,var(--navy) 8px,var(--navy) 11px);}
.nowbar-btn.is-playing .nb-ic-play{display:none;}
.nowbar-btn.is-playing .nb-ic-pause{display:block;}
.nowbar-title{flex:none; max-width:220px; font-size:13px; color:#f0e6d2; text-decoration:none; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.nowbar-title:hover{color:#ffe9c7;}
.nowbar-track{flex:1; min-width:80px; height:6px; background:rgba(255,255,255,.22); border-radius:3px; cursor:pointer; overflow:hidden;}
.nowbar-fill{height:100%; width:0; background:linear-gradient(90deg,#ffe9c7,#e8b96a); border-radius:3px;}
.nowbar-times{flex:none; font-size:12px; color:#d7dde3;}
@media (max-width:720px){
  .hero{padding:46px 0 40px;}
  .clip{padding:8px 10px; gap:9px;}
  .nowbar-inner{padding:8px 12px; gap:10px;}
  .nowbar-title{display:none;}
  .hero h1{font-size:29px;}
  .hero .sub{font-size:17px;}
  .hero .oneline{font-size:14.5px;}
  .wrap{padding:0 15px;}
  #opening .grid{grid-template-columns:1fr;}
  .slide{padding:16px 14px 18px; border-radius:13px;}
  .slide-head{gap:10px;}
  .slide-head .num{font-size:22px; min-width:36px;}
  .slide-head h3{font-size:17px;}
  body{font-size:15.5px;}
  .talk li{padding-left:20px;}
  .sec-head h2{font-size:23px;}
  .path-grid,.numgrid{grid-template-columns:1fr 1fr;}
  .path-card ul{font-size:14px;}
  .path-card li{line-height:1.7;}
  .path-name{font-size:14px;}
  .concl{grid-template-columns:1fr;}
  #chart-map{height:560px;}
  .tl-list li{flex-direction:column; gap:4px;}
  .tl-t{min-width:0;}
}
@media (max-width:420px){
  .path-grid,.numgrid{grid-template-columns:1fr;}
  .mod-row{flex-direction:column; gap:6px;}
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content")
    ap.add_argument("--out", default=None)
    ap.add_argument("--echarts", default=None)
    ap.add_argument("--base", default=None)
    args = ap.parse_args()

    cdir = os.path.dirname(os.path.abspath(args.content))
    base = args.base or cdir
    data = json.load(open(args.content, encoding="utf-8"))

    echarts_path = args.echarts or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "echarts.min.js")

    doc, sl, cc, qq, mm = build(data, base, echarts_path)

    out = args.out or (os.path.splitext(os.path.basename(args.content))[0] + ".html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    print("已生成：%s（%.2f MB）" % (os.path.abspath(out), os.path.getsize(out) / 1e6))
    print("幻灯片=%d 结论=%d 自测=%d 模块=%d" % (sl, cc, qq, mm))


if __name__ == "__main__":
    main()
