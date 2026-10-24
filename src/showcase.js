import { installShowcase } from 'https://cdn.jsdelivr.net/gh/byh-playground/bloom-gamekit@18fdaaf4454be715795fb94f40d8a38aa65e6c41/modules/scenario/showcase-host.js';
installShowcase({
    title:'와르르냥',
    launcher:'[data-screen="main"] [data-route="modes"]',
    playSelector:'[data-screen="main"] [data-route="modes"]',
    durationMs:27500,
    ready:win=>win.document.getElementById('boot')?.classList.contains('hidden')===true,
    timeline:[
  {
    "atMs": 0,
    "action": "chapter",
    "index": 0,
    "title": "작은 고양이의 집안 모험",
    "caption": "사냥하고 구르며 성장해 거대한 탑으로 향합니다."
  },
  {
    "atMs": 500,
    "action": "click",
    "selector": "[data-screen=\"main\"] [data-route=\"modes\"]"
  },
  {
    "atMs": 1150,
    "action": "click",
    "selector": "#startBtn"
  },
  {
    "atMs": 2200,
    "action": "key",
    "code": "KeyW",
    "down": true
  },
  {
    "atMs": 4900,
    "action": "key",
    "code": "KeyW",
    "down": false
  },
  {
    "atMs": 5300,
    "action": "key",
    "code": "ShiftLeft",
    "down": true
  },
  {
    "atMs": 5480,
    "action": "key",
    "code": "ShiftLeft",
    "down": false
  },
  {
    "atMs": 8000,
    "action": "chapter",
    "index": 1,
    "title": "충전 박치기로 물리적 충돌",
    "caption": "누른 시간에 따라 실제 Rapier 강체에 충격을 전달합니다."
  },
  {
    "atMs": 8400,
    "action": "key",
    "code": "KeyF",
    "down": true
  },
  {
    "atMs": 10500,
    "action": "key",
    "code": "KeyF",
    "down": false
  },
  {
    "atMs": 11200,
    "action": "key",
    "code": "KeyD",
    "down": true
  },
  {
    "atMs": 13500,
    "action": "key",
    "code": "KeyD",
    "down": false
  },
  {
    "atMs": 14300,
    "action": "key",
    "code": "KeyF",
    "down": true
  },
  {
    "atMs": 15700,
    "action": "key",
    "code": "KeyF",
    "down": false
  },
  {
    "atMs": 18100,
    "action": "chapter",
    "index": 2,
    "title": "탑이 무너지는 순간까지",
    "caption": "충돌하는 블록과 연쇄 붕괴를 직접 지켜보세요."
  },
  {
    "atMs": 18400,
    "action": "key",
    "code": "KeyW",
    "down": true
  },
  {
    "atMs": 20700,
    "action": "key",
    "code": "KeyW",
    "down": false
  },
  {
    "atMs": 21900,
    "action": "key",
    "code": "Space",
    "down": true
  },
  {
    "atMs": 23000,
    "action": "key",
    "code": "Space",
    "down": false
  },
  {
    "atMs": 23900,
    "action": "key",
    "code": "KeyF",
    "down": true
  },
  {
    "atMs": 26500,
    "action": "key",
    "code": "KeyF",
    "down": false
  }
]
});
