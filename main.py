import os
import asyncio
import random
import schedule
import time

from telethon import TelegramClient, events, functions

# ========== [1] 텔레그램 API 설정 ==========
API_ID = int(os.getenv("API_ID", "22621301"))
API_HASH = os.getenv("API_HASH", "29afe09ac4443720f696cc8e66ca88af")
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "+818029910397")  # 예시 번호

SESSION_NAME = "my_telethon_session"

client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH,
    timeout=60,
    auto_reconnect=True
)

# ========== [2] 파일 경로 설정 ==========
ADVERT_FILE = "advert_message.txt"
IMAGE_FILE = "my_ad_image.jpg"

# 이미 전송한 그룹(채널) 기록
sent_groups = set()

# ========== [3] 광고 문구 로드 함수 ==========
def load_base_message():
    if not os.path.exists(ADVERT_FILE):
        return "광고 문구가 없습니다."
    with open(ADVERT_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()

# ========== [4] 연결확인/재연결 함수 ==========
async def ensure_connected(client: TelegramClient):
    if not client.is_connected():
        print("[INFO] Telethon is disconnected. Reconnecting...")
        await client.connect()

    if not await client.is_user_authorized():
        print("[WARN] 세션 없음/만료 → OTP 로그인 시도")
        await client.start(phone=PHONE_NUMBER)
        print("[INFO] 재로그인(OTP) 완료")

# ========== [5] 주기적 keep_alive(핑) ==========
async def keep_alive(client: TelegramClient):
    try:
        await ensure_connected(client)
        # 아주 가벼운 API 호출
        await client(functions.help.GetNearestDcRequest())
        print("[INFO] keep_alive ping success")
    except Exception as e:
        print(f"[ERROR] keep_alive ping fail: {e}")

def keep_alive_wrapper(client: TelegramClient):
    loop = asyncio.get_running_loop()
    loop.create_task(keep_alive(client))

# ========== [6] '내 계정'이 가입된 그룹/채널 불러오기 ==========
async def load_all_groups(client: TelegramClient):
    await ensure_connected(client)
    dialogs = await client.get_dialogs()
    return [d.id for d in dialogs if d.is_group or d.is_channel]

# ========== [7] 그룹을 10개씩 끊어서 메시지 전송 + 전체 끝난 후 30~40분 대기 ==========
async def send_ad_messages(client: TelegramClient):
    global sent_groups

    try:
        await ensure_connected(client)
        group_list = await load_all_groups(client)

        if not group_list:
            print("[WARN] 가입된 그룹/채널이 없습니다.")
            return

        # 아직 보내지 않은 그룹
        unsent_groups = [g for g in group_list if g not in sent_groups]

        # 보낼 그룹이 없다면 → 모든 그룹 전송 완료 → 초기화 후 다시 전체 대상
        if not unsent_groups:
            print("[INFO] 모든 그룹 전송 완료 상태입니다. sent_groups 초기화하고 다시 시작합니다.")
            sent_groups.clear()
            unsent_groups = group_list[:]  # 전체 그룹 다시 대상

        base_msg = load_base_message()

        # 10개씩 끊어서 전송
        batch_size = 10
        for i in range(0, len(unsent_groups), batch_size):
            batch = unsent_groups[i:i + batch_size]
            print(f"[INFO] 이번에 보낼 그룹: {len(batch)}개 (index={i}~{i+len(batch)-1})")

            # (A) 10개 그룹에 순차적으로 전송
            for grp_id in batch:
                try:
                    if os.path.exists(IMAGE_FILE):
                        await client.send_file(grp_id, IMAGE_FILE, caption=base_msg)
                        print(f"[INFO] (이미지+캡션) 전송 성공 → {grp_id}")
                    else:
                        await client.send_message(grp_id, base_msg)
                        print(f"[INFO] (텍스트만) 전송 성공 → {grp_id}")
                    sent_groups.add(grp_id)

                except Exception as e:
                    print(f"[ERROR] 전송 실패(chat_id={grp_id}): {e}")

            # (B) 한 배치(10개) 전송 후 5~10분 대기
            delay_per_batch = random.randint(300, 600)  # 5~10분
            print(f"[INFO] 다음 10개 그룹 전송 전 {delay_per_batch}초 대기합니다.")
            await asyncio.sleep(delay_per_batch)

        # (C) 모든 unsent_groups를 보냈으면 30~40분 대기
        #     "모든 그룹 다 보냈으면 30-40분 쉬었다가 다시 가자" 요구사항 반영
        rest_time = random.randint(1800, 2400)  # 30~40분
        print(f"[INFO] 모든 그룹 전송 완료. {rest_time // 60}분 대기 후 다음 순회 시작합니다.")
        await asyncio.sleep(rest_time)

    except Exception as e:
        print(f"[ERROR] send_ad_messages 전체 에러: {e}")

# ========== [8] 작업 함수 래퍼 ==========
def job_wrapper(client: TelegramClient):
    loop = asyncio.get_running_loop()
    loop.create_task(send_ad_messages(client))

# ========== [9] 메인(이벤트 루프) ==========
async def main():
    # (1) 연결 시도
    await client.connect()
    print("[INFO] client.connect() 완료")

    # (2) 세션 인증 여부 확인
    if not (await client.is_user_authorized()):
        print("[INFO] 세션 없음 or 만료 → OTP 로그인 시도")
        await client.start(phone=PHONE_NUMBER)
        print("[INFO] 첫 로그인 or 재인증 성공")
    else:
        print("[INFO] 이미 인증된 세션 (OTP 불필요)")

    @client.on(events.NewMessage(pattern="/ping"))
    async def ping_handler(event):
        await event.respond("pong!")

    print("[INFO] 텔레그램 로그인(세션) 준비 완료")

    # 1) 광고 전송: 1시간마다
    schedule.every(60).minutes.do(job_wrapper, client)
    # 2) keep_alive: 10분마다
    schedule.every(10).minutes.do(keep_alive_wrapper, client)

    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())