# 버전 내역
할 일
    ***미션번호 바꾸면 안됨 좌표가 미묘하게 안맞아서 바꾸는건 상관없음***
    정적장애물 구간 lattice 파라미터 튜닝
    첫번째 슬램 구간 lattice 가능하게 (우회전 구간에서 막힘)
    동적장애물 구간 장애물 인식 구현
    주차
    두번째 슬램 구간 lattice 가능하게 (차량 우측에 일자 차단봉 인식 가능하게)
    신호등 인식 (사거리 정지선에서 정지 하는데 거기서 초록불 빨간불 인식 할수 있게)
    
0823

    미션 노드 해당 미션 시작점 가까이가면 그번호로 바뀜 중복가능

0824

    # 미션 4 동적장애물
    # 미션 41 주차
    두개가 다르면 안됨
    미션 8 마무리 했음

    키는법 : kurrier.launch 키고 옆에 kurrierLidar.launch 키면 됨
    kurrier.launch 이거 열어서 output="screen" 이 옵션 달아주면 디버깅 편함
    kurrierLidar.launch 얘가 SLAM 실행시킴

0825

    슬램 시작시 3초 정지후 슬램 키고 시작점 저장하고 다시 3초 대기 후 이동시작
    슬램 끄는거 완료
    키는법 : kurrier.launch 이거만 키면됨
    SaveFile 압축 풀어서 모라이 런처 폴더 안에 모라이 런처 데이터 안에 SaveFile 폴더 대체 하면 됨