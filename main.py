import asyncio
import random
from telethon import TelegramClient
# 구체적인 RPC 예외 클래스를 임포트
from telethon.errors.rpcerrorlist import (
    PeerFloodError,
    UserPrivacyRestrictedError,
    UserAlreadyParticipantError,
    InviteHashExpiredError,
    InviteHashInvalidError,
    UserBannedInChannelError
)
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
            # 링크 형식에 따라 분기 처리
            if 'joinchat' in link or '+' in link:
                # 예: https://t.me/+AbcdEfGh1234xyz
                # 실제 초대 링크의 맨 뒤 해시 부분만 추출
                invite_hash = link.split('/')[-1].replace('+','').replace('joinchat/','')
                await client(ImportChatInviteRequest(invite_hash))
                print(f'[+] 초대 링크로 그룹 가입 성공: {link}')
            else:
                # 공개 그룹/채널 (t.me/채널유저이름)
                channel_username = link.split('/')[-1]
                await client(JoinChannelRequest(channel_username))
                print(f'[+] 공개 그룹/채널 가입 성공: {channel_username}')

            # 5초~15초 사이 랜덤 대기 (너무 빠른 가입 시도 방지)
            wait_time = random.randint(300, 600)
            print(f'[-] 다음 그룹 가입 전 {wait_time}초 대기 중...')
            await asyncio.sleep(wait_time)

        except UserAlreadyParticipantError:
            # 이미 가입되어 있는 그룹
            print(f'[!] 이미 가입된 그룹입니다. (링크: {link}) 다음 그룹으로 넘어갑니다.')
            continue

        except InviteHashExpiredError:
            # 초대 링크가 만료된 경우
            print(f'[!] 초대 링크가 만료되었습니다. (링크: {link}) 다음 그룹으로 넘어갑니다.')
            continue

            # 초대 링크가 잘못된 경우
        except InviteHashInvalidError:
            print(f'[!] 초대 링크가 유효하지 않습니다. (링크: {link}) 다음 그룹으로 넘어갑니다.')
            continue

        except UserBannedInChannelError:
            # 현재 계정이 해당 그룹/채널에서 밴 된 경우
            print(f'[!] 이 그룹(채널)에서 밴 되었습니다. (링크: {link}) 다음 그룹으로 넘어갑니다.')
            continue

        except PeerFloodError:
            # Too Many Requests로 인한 가입 제한
            print(f'[!] 경고: Too Many Requests (PeerFloodError). 텔레그램에서 가입을 제한한 것 같습니다. (링크: {link})')
            print('[!] 일정 시간 대기 후 다시 시도하거나, 나중에 재시도하세요.')
            # 여기서는 예시로 10분 대기 후 다음 링크 시도
            await asyncio.sleep(60 * 10)
            # continue 없이 진행하면, 다음 링크로 넘어가기 전 10분 대기 후 다시 시도할 수도 있음
            # 필요하다면 continue로 바로 다음 링크로 넘길 수도 있음

        except UserPrivacyRestrictedError:
            # 가입이 허용되지 않는 설정
            print(f'[!] 해당 그룹/채널에 가입할 수 없습니다. (User Privacy Restriction) (링크: {link})')
            continue

        except Exception as e:
            # 기타 예외 처리
            print(f'[!] 알 수 없는 오류 발생: {e} (링크: {link})')
            continue

    print("모든 그룹 가입 시도가 완료되었습니다.")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())