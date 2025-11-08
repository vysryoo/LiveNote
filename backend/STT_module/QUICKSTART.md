# 🚀 빠른 시작 가이드

프론트엔드 팀을 위한 STT 서버 5분 셋업 가이드

---

## 📥 1단계: 설치 (30초)

```bash
cd STT_module
chmod +x setup.sh
./setup.sh
```

설치 스크립트가 자동으로:
- ✅ Python 버전 확인
- ✅ 가상환경 생성 (`.venv`)
- ✅ 패키지 설치
- ✅ `.env` 파일 생성

---

## 🔑 2단계: API 키 설정 (1분)

`.env` 파일을 열어서 OpenAI API 키를 입력하세요:

```bash
# .env 파일
OPENAI_API_KEY=sk-your-api-key-here
```

**API 키는 어디서 받나요?**
1. [OpenAI Platform](https://platform.openai.com/api-keys)에 로그인
2. "Create new secret key" 클릭
3. 생성된 키를 복사해서 붙여넣기

---

## 🏃 3단계: 서버 실행 (10초)

```bash
python app.py
```

서버가 정상적으로 실행되면:

```
============================================================
🚀 STT 서버 시작
📍 주소: http://localhost:8003
🔌 WebSocket: ws://localhost:8003/ws/stt
🧪 테스트 페이지: http://localhost:8003/test
🎯 VAD 활성화: True
============================================================
```

---

## 🧪 4단계: 테스트 (1분)

### 방법 1: 내장 테스트 페이지 (추천)

브라우저에서 접속:
```
http://localhost:8003/test
```

### 방법 2: 예제 HTML 파일

브라우저에서 `example_client.html` 파일을 열기

### 방법 3: API 상태 확인

브라우저에서 접속:
```
http://localhost:8003/
```

---

## ✅ 동작 확인

1. "녹음 시작" 버튼 클릭
2. 마이크 권한 허용
3. "안녕하세요" 말하기
4. 전사 결과 확인:
   ```
   📝 안녕하
   ✅ 안녕하세요
   ```

---

## 🎨 프론트엔드 통합

### JavaScript

```javascript
const ws = new WebSocket('ws://localhost:8003/ws/stt');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'transcript_completed') {
    console.log('전사 결과:', data.text);
  }
};
```

### React

```jsx
import useSTT from './useSTT';

function App() {
  const { transcript, startRecording, stopRecording } = useSTT();
  
  return (
    <div>
      <button onClick={startRecording}>시작</button>
      <button onClick={stopRecording}>중지</button>
      <div>{transcript}</div>
    </div>
  );
}
```

자세한 내용은 [`FRONTEND_GUIDE.md`](./FRONTEND_GUIDE.md) 참고

---

## 🔧 설정 변경

### 포트 변경

```bash
# .env 파일
STT_PORT=9000
```

### 언어 변경

```bash
# .env 파일
LANGUAGE=en  # 영어
LANGUAGE=ko  # 한국어 (기본값)
```

### VAD 비활성화

```bash
# .env 파일
VAD_ENABLED=false
```

---

## 🐛 문제 해결

### "OPENAI_API_KEY가 설정되지 않았습니다"

→ `.env` 파일에 API 키 입력

### "OpenAI Realtime API 연결 실패"

→ API 키가 유효한지 확인

### "마이크 권한 오류"

→ 브라우저 설정에서 마이크 권한 허용

### "포트가 이미 사용 중"

→ `.env` 파일에서 다른 포트로 변경

---

## 📚 추가 문서

- [`README.md`](./README.md) - 전체 문서
- [`FRONTEND_GUIDE.md`](./FRONTEND_GUIDE.md) - 프론트엔드 통합 가이드

---

## 💬 문의

문제가 발생하면 팀에 연락하세요!

---

**Happy Coding! 🎉**
