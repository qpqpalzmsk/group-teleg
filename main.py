import asyncio
import random
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import (
    PeerFloodError,
    UserPrivacyRestrictedError,
    UserAlreadyParticipantError,
    InviteHashExpiredError,
    InviteHashInvalidError,
    UserBannedInChannelError,
    FloodWaitError
)
from telethon.errors.common import TypeNotFoundError

from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest

# 텔레그램에서 발급받은 값 입력
api_id = 25705994
api_hash = '6a366c218f441cf58ce607adf14b662a'

# 세션 이름 지정 (원하는 이름, 예: "my_session")
session_name = 'my_session'

async def main():
    # Telethon 클라이언트 생성
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start()  # 첫 실행 시에 전화번호/코드 인증 절차 진행됨

    # 그룹 링크들이 들어있는 파일
    groups_file = 'groups.txt'

    # 파일에서 초대링크들을 한 줄씩 읽어서 가입하기
    with open(groups_file, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    
    for link in lines:
        link = link.strip()
        if not link:
            continue

        try:
            # -------------------------------------------
            # 1) 비공개 초대 링크 vs 공개 링크
            # -------------------------------------------
            if 'joinchat' in link or '+' in link:
                # 비공개 초대 링크 (t.me/+xxx, t.me/joinchat/xxx)
                invite_hash = link.split('/')[-1].replace('+','').replace('joinchat/','')
                await client(ImportChatInviteRequest(invite_hash))
                print(f'[+] 초대 링크(비공개) 가입 성공: {link}')
            else:
                # 공개 그룹/채널 (t.me/채널유저이름)
                channel_username = link.split('/')[-1]
                await client(JoinChannelRequest(channel_username))
                print(f'[+] 공개 그룹/채널 가입 성공: {channel_username}')

            # -------------------------------------------
            # 2) 가입 후 대기 (과도한 가입으로 인한 스팸 판정 방지)
            # -------------------------------------------
            wait_time = random.randint(300, 600)  # 예: 5~10분 사이 랜덤 대기
            print(f'[-] 다음 그룹 가입 전 {wait_time}초 대기 중...')
            await asyncio.sleep(wait_time)

        # ------------------------------------------------------
        # 자주 발생하는 예외들
        # ------------------------------------------------------
        except UserAlreadyParticipantError:
            print(f'[!] 이미 가입된 그룹입니다. (링크: {link}) 다음 그룹으로 넘어갑니다.')
            continue

        except InviteHashExpiredError:
            print(f'[!] 초대 링크가 만료되었습니다. (링크: {link}) 다음 그룹으로 넘어갑니다.')
            continue

        except InviteHashInvalidError:
            print(f'[!] 초대 링크가 유효하지 않습니다. (링크: {link}) 다음 그룹으로 넘어갑니다.')
            continue

        except UserBannedInChannelError:
            print(f'[!] 이 그룹(채널)에서 밴 되었습니다. (링크: {link}) 다음 그룹으로 넘어갑니다.')
            continue

        except UserPrivacyRestrictedError:
            print(f'[!] 해당 그룹/채널에 가입할 수 없습니다 (User Privacy Restriction). (링크: {link})')
            continue

        except FloodWaitError as e:
            print(f'[!] FloodWaitError: 텔레그램에서 {e.seconds}초 동안 대기하라고 합니다. (링크: {link})')
            print(f'[!] {e.seconds}초 후에 다음 링크로 넘어갑니다.')
            await asyncio.sleep(e.seconds)
            continue

        except PeerFloodError:
            print(f'[!] 경고: PeerFloodError (Too Many Requests). (링크: {link})')
            print('[!] 10분 대기 후 다음 링크를 시도합니다.')
            await asyncio.sleep(60 * 10)
            continue

        except TypeNotFoundError as e:
            print(f'[!] Telethon이 지원하지 않는 형식: {e} (링크: {link})')
            print('[!] 해당 링크는 건너뜁니다.')
            continue

        # ------------------------------------------------------
        # 그 외 모든 알 수 없는 오류
        # ------------------------------------------------------
        except Exception as e:
            print(f'[!] 알 수 없는 오류 발생: {e} (링크: {link})')
            print('[!] 해당 링크는 건너뛰고 다음으로 진행합니다.')
            continue

    print("모든 그룹 가입 시도가 완료되었습니다.")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())