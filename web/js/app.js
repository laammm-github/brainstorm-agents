// API 基础 URL
const API_BASE_URL = window.location.origin;

// DOM 元素
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const statusPanel = document.getElementById('statusPanel');

// 状态管理
let isProcessing = false;

/**
 * 开始头脑风暴（使用流式响应）
 */
async function startBrainstorm() {
    const question = userInput.value.trim();
    
    if (!question) {
        alert('请输入问题');
        return;
    }
    
    if (isProcessing) {
        alert('正在处理中，请稍候...');
        return;
    }
    
    // 添加用户消息
    addUserMessage(question);
    
    // 清空输入框
    userInput.value = '';
    
    // 显示加载动画
    showLoading();
    updateStatus('协调者分析问题类型...');
    
    try {
        // 使用流式响应 (SSE)
        const response = await fetch(`${API_BASE_URL}/brainstorm/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: question,
                max_rounds: 2
            }),
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 处理 SSE 流
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) {
                break;
            }
            
            // 解码数据
            buffer += decoder.decode(value, { stream: true });
            
            // 处理 SSE 事件
            const lines = buffer.split('\n');
            buffer = lines.pop(); // 保留不完整的行
            
            for (const line of lines) {
                if (line.startsWith('event:')) {
                    const event = line.slice(6).trim();
                    continue;
                }
                
                if (line.startsWith('data:')) {
                    const dataStr = line.slice(5).trim();
                    if (!dataStr) continue;
                    
                    try {
                        const data = JSON.parse(dataStr);
                        handleSSEEvent(data);
                    } catch (e) {
                        console.error('解析 SSE 数据失败:', e);
                    }
                }
            }
        }
        
        updateStatus('完成');
        
    } catch (error) {
        hideLoading();
        showError(error.message);
        updateStatus('错误');
        console.error('Error:', error);
    }
}

/**
 * 处理 SSE 事件
 */
function handleSSEEvent(data) {
    // 如果是状态更新
    if (data.status === 'classifying') {
        updateStatus('协调者分析问题类型...');
    } else if (data.status === 'debating') {
        updateStatus(`${data.message}`);
    } else if (data.status === 'summarizing') {
        updateStatus('生成综合报告...');
    } else if (data.status === 'role_complete') {
        updateStatus(`${data.role_name} 完成思考`);
    }
    
    // 如果是辩论轮次完成
    if (data.round === 1 && data.results) {
        displayRound('Round 1: 独立思考', data.results);
    } else if (data.round === 2 && data.results) {
        displayRound('Round 2: 交叉辩驳', data.results);
    }
    
    // 如果是最终结果
    if (data.final_report) {
        hideLoading();
        
        // 显示协调者分析
        const analysisDiv = document.createElement('div');
        analysisDiv.className = 'message';
        analysisDiv.innerHTML = `
            <div class="message-header">🔍 协调者分析</div>
            <div class="message-content">
                <p><strong>问题类型：</strong>${data.problem_type}</p>
                <p><strong>使用角色：</strong>${data.selected_roles.join(', ')}</p>
            </div>
        `;
        chatMessages.appendChild(analysisDiv);
        
        // 显示综合报告
        const reportDiv = document.createElement('div');
        reportDiv.className = 'message';
        reportDiv.innerHTML = `
            <div class="message-header">📝 综合报告</div>
            <div class="message-content">${formatReport(data.final_report)}</div>
        `;
        chatMessages.appendChild(reportDiv);
        
        scrollToBottom();
    }
}

/**
 * 添加用户消息
 */
function addUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    messageDiv.innerHTML = `
        <div class="message-header">👤 你</div>
        <div class="message-content">${escapeHtml(text)}</div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * 显示辩论结果
 */
function displayResults(data) {
    // 显示问题类型和角色选择
    const analysisDiv = document.createElement('div');
    analysisDiv.className = 'message';
    analysisDiv.innerHTML = `
        <div class="message-header">🔍 协调者分析</div>
        <div class="message-content">
            <p><strong>问题类型：</strong>${data.problem_type}</p>
            <p><strong>使用角色：</strong>${data.selected_roles.join(', ')}</p>
        </div>
    `;
    chatMessages.appendChild(analysisDiv);
    
    // 显示 Round 1 结果
    displayRound('Round 1: 独立思考', data.debate_results.round_1);
    
    // 显示 Round 2 结果（如果有）
    if (data.debate_results.round_2 && Object.keys(data.debate_results.round_2).length > 0) {
        displayRound('Round 2: 交叉辩驳', data.debate_results.round_2);
    }
    
    // 显示综合报告
    const reportDiv = document.createElement('div');
    reportDiv.className = 'message';
    reportDiv.innerHTML = `
        <div class="message-header">📝 综合报告</div>
        <div class="message-content">${formatReport(data.final_report)}</div>
    `;
    chatMessages.appendChild(reportDiv);
    
    scrollToBottom();
}

/**
 * 显示单轮辩论结果
 */
function displayRound(title, roundData) {
    const roundDiv = document.createElement('div');
    roundDiv.className = 'message';
    
    let content = `<div class="message-header">🎭 ${title}</div><div class="message-content">`;
    
    for (const [color, view] of Object.entries(roundData)) {
        const roleName = getRoleName(color);
        const roleEmoji = getRoleEmoji(color);
        content += `
            <div style="margin-bottom: 12px;">
                <strong>${roleEmoji} ${roleName}</strong>
                <div style="margin-top: 6px; padding-left: 12px; border-left: 3px solid var(--${color}-hat); text-align: left;">
                    ${escapeHtml(view)}
                </div>
            </div>
        `;
    }
    
    content += '</div>';
    roundDiv.innerHTML = content;
    chatMessages.appendChild(roundDiv);
}

/**
 * 格式化报告（简单的 Markdown 转换）
 */
function formatReport(report) {
    // 将 ## 转换为 <h3>
    report = report.replace(/## (.+)/g, '<h3>$1</h3>');
    
    // 将 - 或 * 列表项转换为 <ul>
    report = report.replace(/^[\-\*] (.+)$/gm, '<li>$1</li>');
    report = report.replace(/(<li>.+<\/li>\n?)+/g, '<ul>$&</ul>');
    
    // 将数字列表项转换为 <ol>
    report = report(/^\d+\. (.+)$/gm, '<li>$1</li>');
    
    // 换行转换
    report = report.replace(/\n/g, '<br>');
    
    return report;
}

/**
 * 获取角色名称
 */
function getRoleName(color) {
    const names = {
        'white': '白帽',
        'red': '红帽',
        'black': '黑帽',
        'yellow': '黄帽',
        'green': '绿帽',
        'purple': '紫帽'
    };
    return names[color] || color;
}

/**
 * 获取角色表情符号
 */
function getRoleEmoji(color) {
    const emojis = {
        'white': '⚪',
        'red': '🔴',
        'black': '⚫',
        'yellow': '🟡',
        'green': '🟢',
        'purple': '🟣'
    };
    return emojis[color] || '⚪';
}

/**
 * 显示加载动画
 */
function showLoading() {
    isProcessing = true;
    sendBtn.disabled = true;
    
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.id = 'loadingIndicator';
    loadingDiv.innerHTML = `
        <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    chatMessages.appendChild(loadingDiv);
    scrollToBottom();
}

/**
 * 隐藏加载动画
 */
function hideLoading() {
    isProcessing = false;
    sendBtn.disabled = false;
    
    const loadingDiv = document.getElementById('loadingIndicator');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

/**
 * 更新状态面板
 */
function updateStatus(status) {
    statusPanel.innerHTML = `<p>${status}</p>`;
}

/**
 * 显示错误消息
 */
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'message error-message';
    errorDiv.innerHTML = `
        <div class="message-header">❌ 错误</div>
        <div class="message-content" style="color: red;">${escapeHtml(message)}</div>
    `;
    chatMessages.appendChild(errorDiv);
    scrollToBottom();
}

/**
 * 滚动到底部
 */
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * HTML 转义
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 监听 Enter 键（Ctrl+Enter 发送）
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
        startBrainstorm();
    }
});

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎭 头脑风暴智能体已加载');
    updateStatus('就绪');
});
