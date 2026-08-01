function submitToken() {
    const token = document.getElementById('tokenInput').value.trim();
    const resultDiv = document.getElementById('result');
    
    if (!token) {
        resultDiv.innerText = '⚠️ Vui lòng nhập Access Token.';
        resultDiv.className = 'result-box error';
        return;
    }

    resultDiv.innerText = '⏳ Đang gửi...';
    resultDiv.className = 'result-box';

    fetch('/submit_token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: token })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            resultDiv.innerHTML = '✅ Token đã gửi đến admin. Vui lòng chờ xử lý.';
            resultDiv.className = 'result-box success';
            document.getElementById('tokenInput').value = '';
        } else {
            resultDiv.innerHTML = '❌ ' + data.msg;
            resultDiv.className = 'result-box error';
            // Nếu chưa đăng nhập, chuyển hướng sau 2s
            if (data.msg.includes('đăng nhập')) {
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            }
        }
    })
    .catch(error => {
        resultDiv.innerText = '❌ Không kết nối được server.';
        resultDiv.className = 'result-box error';
        console.error(error);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('tokenInput');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') submitToken();
        });
    }
});