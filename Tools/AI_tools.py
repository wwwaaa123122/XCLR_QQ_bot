import re
import time
import random
from collections import defaultdict
from datetime import datetime

class StreamSplitter:
    def __init__(self):
        # # 正则表达式
        # self.number_re = re.compile(r'^\s*(\d+)[.)]\s+')
        self.full_content = ""
        
        # # 状态初始化（新增last_split_time）
        # self.last_number = None
        # self.pending_newlines = 0
        # self.message_buffer = []
        # self.newline_records = []
        self.last_split_time = time.time()  # 初始化时间戳
        
        self.forward_msg_num = 500
        self.enable_forward_msg_num = False
        self.check_forward_msg = False
        
        # 分割依据
        self.split_str = "\n\n\n\n"
        self.chunks = 0
        self.buffer = ""
        
    def split_stream(self, response_stream, type='gemini'):
        try:
            for chunk in response_stream:
                match type:
                    case 'gemini':
                        chunk_text = chunk.text
                    case 'openai':
                        chunk_text = chunk.choices[0].delta.content
                        
                self.full_content += chunk_text
                self.buffer += chunk_text
                self.chunks += 1
                if time.time() - self.last_split_time >= 1.5:
                    self.last_split_time = time.time()
                    for r in self.check_and_split():
                        if r != "":
                            yield r, self.enable_forward_msg_num
                        
            for r in self.check_and_split(True):
                yield r, self.enable_forward_msg_num
                
            print(f"[{datetime.now()}] FULL_CONTENT: {repr(self.full_content)}")
        except:
            raise
    
    def check_and_split(self, last_response=False):
        if not self.check_forward_msg:
            if len(self.buffer) > self.forward_msg_num:
                self.enable_forward_msg_num = True
            self.check_forward_msg = True
            
        messages = []
        if self.split_str == "\n\n\n\n":
            for sep in (self.split_str[:i] for i in range(4, -1, -1)):
                if sep in self.buffer:
                    self.split_str = sep
                    break
                
        if self.split_str == "":
            self.split_str = "\n\n\n\n"
            message = self.buffer
            
        else:
            messages = self.buffer.split(self.split_str)
            
            if not last_response:
                message = messages[0]
            else:
                for m in messages:
                    yield m
                    time.sleep(random.uniform(0.5, 2.0))
                return
            
            self.buffer = ""
            
            if len(messages) == 1:
                self.buffer = messages[0]
            else:
                for i in range(len(messages)-1):
                    self.buffer = self.buffer + messages[i+1] + "\n"

        yield message