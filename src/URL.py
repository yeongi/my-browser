import socket
import ssl


class URL:
    def __init__(self, url: str):

        self.scheme, remainder = url.split("://", 1)
        assert self.scheme in ["http", "https"]

        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        if "/" not in remainder:
            remainder = f"{remainder}/"

        self.host, path = remainder.split("/", 1)
        self.path = f"/{path}"


        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def request(self) -> str:
        # 소켓을 정의하고 연결한다.
        sock = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )

        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(sock, server_hostname=self.host)

        sock.connect((self.host, self.port))

        # 요청을 작성하고 전송한다.
        request = f"GET {self.path} HTTP/1.0\r\n"
        request += f"Host: {self.host}\r\n"
        request += "\r\n"

        sock.send(request.encode("utf8"))

        # 응답을 수신한다.
        response = sock.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        # 상태 줄 다음에는 헤더가 있다.
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        # 특히 중요한 헤더는 검증
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        # 전송된 데이터를 얻는 방법은 헤더 다음의 모든 데이터를 가져온다.
        body = response.read()
        sock.close()

        # 이 내용이 화면에 그려야 할 바디
        return body


def show(body: str) -> None:
    in_tag = False
    for char in body:
        if char == "<":
            in_tag = True
        elif char == ">":
            in_tag = False            
        elif not in_tag:
            print(char, end="")


def load(url: URL) -> None:
    body = url.request()
    show(body)

if __name__ == "__main__":
    import sys
    load(URL(sys.argv[1]))