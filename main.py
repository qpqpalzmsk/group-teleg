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

# 텔레그램 API 정보
api_id = 22621301
api_hash = '29afe09ac4443720f696cc8e66ca88af'

# 세션 이름
session_name = 'my_session'

# 처리할 5개 텍스트 파일 목록 (미리 만들어 두세요: groups1.txt, groups2.txt, ... groups5.txt)
file_list = [
    'groups1.txt',
    'groups2.txt',
    'groups3.txt',
    'groups4.txt',
    'groups5.txt'
]

# 각 그룹 가입 후 기다릴 시간 (초)
JOIN_DELAY_MIN = 600
JOIN_DELAY_MAX = 850

# 다음 파일로 넘어가기 전 24시간(86400초) 대기
WAIT_BETWEEN_FILES = 86400  # 24시간

async def join_groups_in_file(client, groups_file):
    """
    하나의 텍스트 파일(groups_file)에 적힌 링크들을 가입 시도하는 함수.
    """
    with open(groups_file, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    for link in lines:
        link = link.strip()
        if not link:
            continue

        try:
            # 비공개 초대 링크 여부 확인
            if 'joinchat' in link or '+' in link:
                invite_hash = link.split('/')[-1].replace('+','').replace('joinchat/','')
                await client(ImportChatInviteRequest(invite_hash))
                print(f'[+] 비공개 초대 링크 가입 성공: {link}')
            else:
                # 공개 그룹/채널
                channel_username = link.split('/')[-1]
                await client(JoinChannelRequest(channel_username))
                print(f'[+] 공개 그룹/채널 가입 성공: {channel_username}')

            # 가입 후 짧은 대기 (스팸 의심 완화)
            wait_time = random.randint(JOIN_DELAY_MIN, JOIN_DELAY_MAX)
            print(f'[-] 다음 가입 전 {wait_time}초 대기 중...')
            await asyncio.sleep(wait_time)

        except UserAlreadyParticipantError:
            print(f'[!] 이미 가입된 그룹: {link} → 다음 링크로 넘어갑니다.')
            continue
        except InviteHashExpiredError:
            print(f'[!] 초대 링크 만료: {link} → 다음 링크.')
            continue
        except InviteHashInvalidError:
            print(f'[!] 초대 링크가 유효하지 않음: {link} → 다음 링크.')
            continue
        except UserBannedInChannelError:
            print(f'[!] 해당 채널에서 밴 당함: {link} → 다음 링크.')
            continue
        except UserPrivacyRestrictedError:
            print(f'[!] 가입 불가 (User Privacy Restriction): {link} → 다음 링크.')
            continue
        except FloodWaitError as e:
            print(f'[!] FloodWaitError: 텔레그램에서 {e.seconds}초 대기 요구. (링크: {link})')
            print('[!] 대기 후 다음 링크로 넘어갑니다.')
            await asyncio.sleep(e.seconds)
            continue
        except PeerFloodError:
            print(f'[!] PeerFloodError: 너무 빠른 가입 시도로 제한됨. (링크: {link})')
            print('[!] 15분 대기 후 진행.')
            await asyncio.sleep(900)
            continue
        except TypeNotFoundError as e:
            print(f'[!] Telethon 미지원 형식 (Constructor ID...) → {e} / 링크: {link}')
            print('[!] 다음 링크로 넘어갑니다.')
            continue
        except Exception as e:
            print(f'[!] 기타 오류 발생: {e} (링크: {link}) → 다음 링크로 넘어갑니다.')
            continue

async def main():
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start()

    for i, groups_file in enumerate(file_list):
        print(f"\n=== 파일 {i+1}/{len(file_list)}: {groups_file} 처리 시작 ===\n")

        # 이 파일의 링크들에 대해 가입 시도
        await join_groups_in_file(client, groups_file)

        # 마지막 파일이 아니라면 24시간 대기 후 다음 파일로 넘어감
        if i < len(file_list) - 1:
            print(f"\n[파일 {i+1} 처리 완료] 다음 파일로 넘어가기 전 24시간 대기합니다...\n")
            await asyncio.sleep(WAIT_BETWEEN_FILES)

    print("\n모든 파일에 대한 가입 시도가 완료되었습니다. 프로그램을 종료합니다.")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
