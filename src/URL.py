import socket
import ssl
import tkinter
import tkinter.font

WIDTH , HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
FONTS = {}

def get_font(size, weight, style):
    key = (size, weight, style)
    if key not in FONTS:
        font = tkinter.font.Font(size = size, weight=weight, slant=style)
        label = tkinter.Label(font=font)
        FONTS[key] = (font,label)
    return FONTS[key][0]


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT   
        )
        self.canvas.pack()
        self.scroll = 0

        # scroll 바인딩
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Up>", self.scroll_up)

    def load(self, url):
        body = url.request()
        tokens = lex(body)
        self.display_list = Layout(tokens).display_list
        self.draw()

        # self.canvas.create_rectangle(10,20,400,300)
        # self.canvas.create_oval(100, 100, 150, 150)
        # self.canvas.create_text(200,150, text="Hi!")

        # cursor_x, cursor_y = HSTEP, VSTEP

        # for c in text:
        #     self.canvas.create_text(cursor_x, cursor_y, text=c)
        #     cursor_x += HSTEP
        #     if cursor_x >= WIDTH - HSTEP:
        #         cursor_x = HSTEP
        #         cursor_y += VSTEP


    def scroll_up(self, event):
        self.scroll -= SCROLL_STEP
        if self.scroll < 0:
            self.scroll = 0
        self.draw()

    def scroll_down(self, event):
        self.scroll += SCROLL_STEP
        self.draw()

    def draw(self):
        self.canvas.delete("all")

        for x,y,c,font in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y-self.scroll, text=c, anchor="nw", font=font)


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
            sock = ctx.wrap_socket(sock, server_hostname=self.host)

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

class Text:
    def __init__(self, text):
        self.text = text

class Tag:
    def __init__(self,tag):
        self.tag = tag

def lex(body: str) -> str:
    out = []
    buffer = ""
    in_tag = False
    for char in body:
        if char == "<":
            in_tag = True
            if buffer: out.append(Text(buffer))
            buffer = ""
        elif char == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer = ""
        else:
            buffer += char
    if not in_tag and buffer:
        out.append(Text(buffer))
        
    return out

class Layout:
    def __init__(self, tokens):
        self.display_list = []
        self.size = 12
        self.line = []

        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"

        for tok in tokens:
            self.token(tok)
        
        self.flush()

    def token(self, tok):
        if(isinstance(tok, Text)):
       
            for word in tok.text.split():
                font = tkinter.font.Font(
                    size=self.size,
                    weight=self.weight,
                    slant=self.style
                )
                self.display_list.append((self.cursor_x, self.cursor_y, word, font))

                w = font.measure(word)
                self.cursor_x += w + font.measure(" ")
                if self.cursor_x >= WIDTH - HSTEP:
                    self.cursor_x = HSTEP
                    self.cursor_y += font.metrics("linespace") * 1.25

        elif (isinstance(tok, Tag)):
            if(tok.tag == "i"):
                self.style = "italic"
            elif(tok.tag == "/i"):
                self.style = "roman"
            elif(tok.tag == "b"):
                self.weight = "bold"
            elif(tok.tag == "/b"):
                self.weight = "normal"
            elif(tok.tag == "small"):
                self.size-=2
            elif(tok.tag == "/small"):
                self.size+=2
            elif(tok.tag == "big"):
                self.size += 4
            elif(tok.tag == "/big"):
                self.size -=4
            elif(tok.tag == "br"):
                self.flush()
            elif(tok.tag == "/p"):
                self.flush()
                self.cursor_y += VSTEP


    def word(self, word):
        font = get_font(self.size, self.weight, self.style)
        w = font.measure(word)

        if(self.cursor_x + w > WIDTH - HSTEP):
            self.flush()

    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))

        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

        self.cursor_x = HSTEP
        self.line = []


if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()

