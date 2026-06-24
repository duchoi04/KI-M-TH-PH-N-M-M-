import threading
import time

# ==========================================
# 1. KHAI BÁO HỆ THỐNG (Action-State Model)
# ==========================================
class AuthenticationGuard:
    def __init__(self):
        self.state = 'Active'
        self.failed_attempts = 0

    def process_action(self, action):
        time.sleep(0.1)  # Giả lập độ trễ mạng/Database
        
        if self.state == 'Active':
            if action == 'Login_Success':
                self.failed_attempts = 0
                return "Redirect_Dashboard"
                
            elif action == 'Login_Fail':
                # ĐIỂM YẾU GÂY LỖI: Không dùng cơ chế Lock khi cập nhật biến
                current_attempts = self.failed_attempts
                time.sleep(0.05) # Context switch (khe hở thời gian để các luồng ghi đè nhau)
                self.failed_attempts = current_attempts + 1
                
                if self.failed_attempts >= 3:
                    self.state = 'Temporarily_Locked'
                    return "Show_Lock_Msg"
                return "Show_Error_Msg"
                
        elif self.state == 'Temporarily_Locked':
            if action == 'Login_Success':
                return "Reject_Access_Error"
            elif action == 'Unlock_Trigger':
                self.state = 'Active'
                self.failed_attempts = 0
                return "Send_SMS_Noti"
        
        return "Invalid_Action"

# ==========================================
# 2. KỊCH BẢN KIỂM THỬ (Thực thi và đánh giá)
# ==========================================
if __name__ == "__main__":
    guard = AuthenticationGuard()
    
    print("="*60)
    print(f"TRẠNG THÁI BAN ĐẦU: {guard.state} | Số lần sai: {guard.failed_attempts}")
    print("="*60)
    
    def send_request(action, thread_name):
        print(f"[{thread_name}] Đang gửi request: {action}...")
        result = guard.process_action(action)
        print(f"[{thread_name}] Kết quả: {result: <20} | Trạng thái sau đó: {guard.state} | Tổng lỗi ghi nhận: {guard.failed_attempts}")

    print("\n[TC02 - BƯỚC 1]: Người dùng đăng nhập sai 1 lần (Luồng bình thường)")
    send_request('Login_Fail', 'User_Normal')
    
    print("\n" + "-"*60)
    print("[TC02 - BƯỚC 2]: TẤN CÔNG RACE CONDITION (Kiểm thử bất đồng bộ)")
    print("Mô phỏng Hacker dùng Tool bắn 2 request 'Login_Fail' cùng lúc vào hệ thống...")
    print("-" * 60)
    
    # Tạo 2 luồng (thread) chạy song song đâm cùng lúc vào hệ thống
    t1 = threading.Thread(target=send_request, args=('Login_Fail', 'Hacker_Thread_1'))
    t2 = threading.Thread(target=send_request, args=('Login_Fail', 'Hacker_Thread_2'))
    
    # Kích hoạt 2 luồng chạy đồng thời
    t1.start()
    t2.start()
    
    # Đợi cả 2 luồng chạy xong mới đi tiếp
    t1.join()
    t2.join()
    
    print("\n" + "="*60)
    print("ĐÁNH GIÁ KẾT QUẢ KIỂM THỬ (REPORT)")
    print("="*60)
    print("1. Theo thiết kế lý thuyết:") 
    print("   Đã sai 1 lần + bắn thêm 2 lần = 3 lần sai.")
    print("   Trạng thái ĐÚNG RA phải chuyển thành: Temporarily_Locked")
    print(f"\n2. Trạng thái THỰC TẾ hệ thống đang ghi nhận: {guard.state}")
    print(f"   Tổng số lỗi lưu trong Database: {guard.failed_attempts}")
    print("\n=> KẾT LUẬN: Đã bắt được lỗi Race Condition!")
    print("=> Hệ thống bị qua mặt vì biến trạng thái bị ghi đè đồng thời. Tài khoản không bị khóa như kỳ vọng.")