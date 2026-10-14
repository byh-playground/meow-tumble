# 와르르냥 / Meow Tumble

집 안을 누비는 작은 고양이가 쥐·곤충을 사냥하며 성장하고, 거인의 공격을 피하며 거대한 젠가탑을 무너뜨리는 **Rapier 3D 물리 게임**입니다. 블록이 무너지는 마지막 순간까지 관전하세요.

**[▶ 바로 플레이 / Play now](https://byh-playground.github.io/meow-tumble/)** · **v0.10.3** · PC / 터치 · 1–4명

![실제 Edge에서 실행한 와르르냥](docs/gameplay.png)

A small cat hunts around a house, grows heavier, dodges giants, and topples a tower through real rigid-body physics. Watch the collapse unfold before the result screen.

## 조작

| 행동 | PC | 터치 |
| --- | --- | --- |
| 이동 / 시점 | WASD·방향키 / 마우스 이동 | 왼쪽 스틱 / 오른쪽 드래그 |
| 할퀴기 / 박치기 | F·좌클릭 짧게 / 길게 누른 뒤 놓기 | 발바닥 버튼 탭 / 홀드 |
| 점프 / 구르기 | Space 홀드 후 놓기 / Shift | 점프 홀드 / 구르기 버튼 |

시작하기 → 혼자 시작, 또는 친구와 함께 → 방 만들기·4자리 코드 참가 → 방장이 시작합니다. 도움말·설정은 별도 화면이며, 플레이 중 지도·상세 버튼으로 추가 HUD를 확인합니다. 결과 화면에서는 방장이 다시 시작하거나 각자 타이틀로 돌아갈 수 있습니다. 최고 레벨은 12이며 도달하면 MAX로 표시합니다. HP가 0이면 현재 레벨 구간 XP의 10%를 잃고 경계를 넘으면 레벨이 내려갑니다 (최저 1). 만렙에서는 11→12 구간을 기준으로 차감하고 초과 XP는 쌓이지 않습니다. 탑 진행도는 유지하며 부활합니다. Esc로 마우스 잠금을 해제합니다.

## 실행과 구성

`index.html` 하나가 현행 소스이자 배포 파일입니다. 빌드가 없습니다. 저장소에서 `python -m http.server 8080`을 실행한 뒤 http://localhost:8080 에 접속합니다. WebGL 및 외부 GameKit·Rapier CDN 접속이 필요합니다. 멀티플레이에는 공개 Nostr relay와 WebRTC 연결이 필요합니다.

GameKit **v0.3.1**, dist `72b09b260edf9650353017acb49c06873fe9f5a1`에 고정합니다. 입력·루프·PRNG·방/세션·보간·확정 표시 이벤트를 SDK가 맡고, 호스트의 Rapier 월드가 싱글/멀티의 같은 게임 규칙을 실행합니다. 게스트 보간은 표시 전용이며 별도 이동 시뮬레이션을 만들지 않습니다. 의존성 해시는 [dependencies.json](docs/dependencies.json)에 있습니다.

## 검증과 배포

Windows Edge와 실제 Rapier·GameKit, 서로 분리된 두 브라우저의 실제 Nostr/WebRTC 연결로 대표 흐름을 확인합니다. 이동·양쪽 경사로·구르기·방 참가·멀티 이동·재시작이 검증 대상입니다. HP 0와 붕괴는 실제 엔진을 사용하는 통제된 상태 경계 시나리오도 별도로 확인합니다. 상세 결과와 한계는 [이관 PR #1](https://github.com/byh-playground/meow-tumble/pull/1)에 기록했습니다. 외부 NAT 간 연결, 4인, 모바일 실기기, 장시간 밸런스는 미검증입니다.

Actions는 PR에서 배포 파일을 준비하고, main 병합 후 Pages에 같은 HTML을 배포합니다. 회귀 스크립트는 임시 검증 환경에서 실행하고 저장소에 남기지 않습니다.

## 출처와 관리

원본 `do_meow_no_house_raid_v0_9_3.html`의 크기·SHA-256·출처·최초 커밋은 [origin.json](docs/origin.json)에 보존합니다. 원본 코드는 최초 커밋에서 볼 수 있으며 실행 복사본을 중복 유지하지 않습니다. 원본의 절차적 집·고양이 렌더, Rapier 물리, 조작과 붕괴 관전을 유지했습니다.

0.10.0은 원격 동작·전투 이벤트 패킷 변경으로 이전 방과 호환되지 않는 MINOR 변경입니다. 전역/캐릭터 부활 타이머 중복, 원격 HP 차이로 타격을 추정하던 경로, 별도 게스트 이동 예측, 재시작 시 물리 큐 누수를 정리했습니다.

[개발 규칙](https://github.com/byh-playground/bloom-reference/blob/main/rules/development.html) · [관리 규칙](https://github.com/byh-playground/bloom-reference/blob/main/rules/project-management.html) · [UI/UX 규칙](https://github.com/byh-playground/bloom-reference/blob/main/rules/visual-ux.html)

이 저장소에 새 프로젝트 라이선스를 임의로 부여하지 않았습니다. 외부 [Rapier 0.21.0](https://github.com/dimforge/rapier.js) 및 [Bloom GameKit](https://github.com/byh-playground/bloom-gamekit)의 기존 권리·고지를 유지합니다. 집·고양이·효과는 원본의 절차적 그래픽이며 별도 이미지 에셋으로 교체하지 않았습니다.

## GameKit 0.3.1 후보 검증

0.10.1은 SDK 배포 pin과 공식 모듈 해시만 갱신한 호환 PATCH입니다. 게임 규칙·30TPS·기존 방 namespace를 유지합니다. [현재 로컬 결과](docs/verification-sdk031.json)는 Chromium 시작 단계의 실행 환경 차단이며 게임 PASS가 아닙니다. 기존 Edge 검증은 위에 별도 역사 기록으로 유지합니다. 사용자 요청에 따라 이번 호환 PATCH는 정적 코드·빌드 검증으로 배포하며, 실제 브라우저 재검증은 추후 사용자 확인으로 남깁니다.

## 메뉴 정리 0.10.2 (후보)

타이틀·모드 선택·대기실·도움말·설정을 GameKit navigation의 hash 화면으로 분리합니다. 주소 진입과 이력 복원은 게임 시작·방 종료를 실행하지 않습니다. 플레이 중 도움말·설정은 입력만 차단하며 세계는 계속 움직입니다. 기존 게임 규칙·네트워크 계약은 유지하는 호환 PATCH입니다. 실제 브라우저 검증 및 배포 상태는 해당 PR에 기록합니다.

## 성장 확장 0.10.3 (후보)

1–8 레벨의 XP 문턱과 위력을 보존하고 최고 레벨을 12로 확장합니다. 새 누적 XP 문턱은 47/58/70/83이며 질량은 레벨당 ×1.5, 박치기 기본속도는 +5/7씩 기존 추세를 연장합니다. 사망 XP 손실은 소수 첫째 자리까지 적용되며 호스트의 한 번의 사망 전이에서만 차감합니다. 스냅샷 형식은 유지합니다. 실제 브라우저 검증과 배포 상태는 해당 PR에서 확인합니다.

고양이 외형·충돌 반지름은 기존 기본 크기 대비 LV1 60%에서 LV12 120%까지 선형 성장합니다. 레벨 하락도 같은 크기·질량 경로를 사용하며 발 위치를 유지합니다. 할퀴기 판정·그림자·전신 회전·이름표·카메라 주시 높이도 크기를 따릅니다.
