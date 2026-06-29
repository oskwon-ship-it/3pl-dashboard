import bcrypt

print("====================================")
print("🔑 비밀번호 암호화 생성기")
print("====================================")
pw = input("새로 설정할 비밀번호를 입력하세요: ")

hashed_pw = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

print("\n아래의 암호화된 문자열을 복사해서 config.yaml 파일의 password 란에 붙여넣으세요:\n")
print(hashed_pw)
print("\n====================================")
