// ============================================================
// API CONFIGURATION
// ============================================================

const API_BASE_URL = "http://127.0.0.1:8000";


// ============================================================
// STATE
// ============================================================

let conversationId = null;


// ============================================================
// DOM ELEMENTS
// ============================================================

const newChatButton =
    document.getElementById("newChatButton");

const conversationList =
    document.getElementById("conversationList");

const connectionStatus =
    document.getElementById("connectionStatus");

const chatMessages =
    document.getElementById("chatMessages");

const chatForm =
    document.getElementById("chatForm");

const questionInput =
    document.getElementById("questionInput");

const sendButton =
    document.getElementById("sendButton");

const sendText =
    document.getElementById("sendText");

const loadingText =
    document.getElementById("loadingText");


// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        attachExampleQuestionEvents();

        setupTextarea();

        await loadConversations();

    }
);


// ============================================================
// LOAD ALL CONVERSATIONS
// ============================================================

async function loadConversations() {

    try {

        setConnectionStatus(
            "loading",
            "Loading conversations..."
        );

        const response =
            await fetch(
                `${API_BASE_URL}/api/conversations`
            );

        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }

        const data =
            await response.json();

        if (!data.success) {

            throw new Error(
                "Failed to load conversations."
            );

        }

        const conversations =
            data.conversations || [];

        renderConversations(
            conversations
        );

        setConnectionStatus(
            "connected",
            "Connected"
        );

    }
    catch (error) {

        console.error(
            "Failed to load conversations:",
            error
        );

        setConnectionStatus(
            "error",
            "Backend unavailable"
        );

        showConversationError();

    }

}


// ============================================================
// RENDER CONVERSATIONS
// ============================================================

function renderConversations(
    conversations
) {

    conversationList.innerHTML = "";

    if (
        !conversations ||
        conversations.length === 0
    ) {

        showEmptyConversations();

        return;

    }

    conversations.forEach(
        conversation => {

            addConversation(
                conversation
            );

        }
    );

}


// ============================================================
// ADD CONVERSATION TO SIDEBAR
// ============================================================

function addConversation(
    conversation,
    prepend = false
) {

    if (!conversation) {
        return;
    }

    const id =
        conversation.conversation_id;

    if (!id) {
        return;
    }

    let item =
        document.querySelector(
            `[data-conversation-id="${id}"]`
        );

    // --------------------------------------------------------
    // If already exists, update its title
    // --------------------------------------------------------

    if (item) {

        const titleElement =
            item.querySelector(
                ".conversation-title"
            );

        if (titleElement) {

            titleElement.textContent =
                conversation.title ||
                "New BI Analysis";

        }

        return item;

    }

    // --------------------------------------------------------
    // Remove empty-state message
    // --------------------------------------------------------

    const empty =
        document.querySelector(
            ".empty-conversations"
        );

    if (empty) {
        empty.remove();
    }

    // --------------------------------------------------------
    // Create conversation wrapper
    // --------------------------------------------------------

    item =
        document.createElement(
            "div"
        );

    item.className =
        "conversation-item";

    item.dataset.conversationId =
        id;

    // --------------------------------------------------------
    // Conversation title
    // --------------------------------------------------------

    const title =
        document.createElement(
            "span"
        );

    title.className =
        "conversation-title";

    title.textContent =
        conversation.title ||
        "New BI Analysis";

    // --------------------------------------------------------
    // Delete button
    // --------------------------------------------------------

    const deleteButton =
        document.createElement(
            "button"
        );

    deleteButton.type =
        "button";

    deleteButton.className =
        "conversation-delete";

    deleteButton.title =
        "Delete conversation";

    deleteButton.setAttribute(
        "aria-label",
        "Delete conversation"
    );

    deleteButton.innerHTML =
        "🗑";

    // --------------------------------------------------------
    // Delete event
    // --------------------------------------------------------

    deleteButton.addEventListener(
        "click",
        async event => {

            event.preventDefault();

            event.stopPropagation();

            await deleteConversation(
                id,
                item
            );

        }
    );

    // --------------------------------------------------------
    // Select conversation event
    // --------------------------------------------------------

    item.addEventListener(
        "click",
        async event => {

            if (
                event.target.closest(
                    ".conversation-delete"
                )
            ) {
                return;
            }

            console.log(
                "CLICKED CONVERSATION:",
                id
            );

            await selectConversation(
                id,
                item
            );

        }
    );

    // --------------------------------------------------------
    // Build item
    // --------------------------------------------------------

    item.appendChild(
        title
    );

    item.appendChild(
        deleteButton
    );

    // --------------------------------------------------------
    // Add to sidebar
    // --------------------------------------------------------

    if (prepend) {

        conversationList.prepend(
            item
        );

    }
    else {

        conversationList.appendChild(
            item
        );

    }

    return item;

}


// ============================================================
// DELETE CONVERSATION
// ============================================================

async function deleteConversation(
    id,
    item = null
) {

    if (!id) {
        return;
    }

    const confirmed =
        window.confirm(
            "Are you sure you want to delete this conversation?"
        );

    if (!confirmed) {
        return;
    }

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/conversations/${encodeURIComponent(id)}`,
                {
                    method: "DELETE"
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.message ||
                `HTTP ${response.status}`
            );

        }

        // ----------------------------------------------------
        // Remove sidebar item
        // ----------------------------------------------------

        if (item) {
            item.remove();
        }

        // ----------------------------------------------------
        // If current conversation was deleted
        // ----------------------------------------------------

        if (
            conversationId === id
        ) {

            conversationId =
                null;

            showWelcomeMessage();

            questionInput.value = "";

            resetTextareaHeight();

            questionInput.focus();

        }

        // ----------------------------------------------------
        // Check if sidebar is empty
        // ----------------------------------------------------

        const remaining =
            document.querySelectorAll(
                ".conversation-item"
            );

        if (
            remaining.length === 0
        ) {

            showEmptyConversations();

        }

        console.log(
            "CONVERSATION DELETED:",
            id
        );

    }
    catch (error) {

        console.error(
            "Delete conversation error:",
            error
        );

        alert(
            `Unable to delete conversation.\n\n${error.message}`
        );

    }

}


// ============================================================
// SELECT CONVERSATION
// ============================================================

async function selectConversation(
    id,
    item = null
) {

    if (!id) {
        return;
    }

    console.log(
        "SELECT CONVERSATION:",
        id
    );

    // --------------------------------------------------------
    // Save selected conversation
    // --------------------------------------------------------

    conversationId =
        id;

    // --------------------------------------------------------
    // Active sidebar item
    // --------------------------------------------------------

    document
        .querySelectorAll(
            ".conversation-item"
        )
        .forEach(
            element => {

                element.classList.remove(
                    "active"
                );

            }
        );

    if (item) {

        item.classList.add(
            "active"
        );

    }
    else {

        const selectedItem =
            document.querySelector(
                `[data-conversation-id="${id}"]`
            );

        if (selectedItem) {

            selectedItem.classList.add(
                "active"
            );

        }

    }

    // --------------------------------------------------------
    // Loading state
    // --------------------------------------------------------

    showConversationLoading();

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/conversations/${encodeURIComponent(id)}`
            );

        console.log(
            "HTTP STATUS:",
            response.status
        );

        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }

        const data =
            await response.json();

        console.log(
            "LOADED CONVERSATION:",
            data
        );

        if (!data.success) {

            throw new Error(
                data.detail ||
                data.message ||
                "Failed to load conversation."
            );

        }

        // ----------------------------------------------------
        // Saved messages and analyses
        // ----------------------------------------------------

        const messages =
            data.messages || [];

        const analyses =
            data.analyses || [];

        console.log(
            "MESSAGES COUNT:",
            messages.length
        );

        console.log(
            "ANALYSES COUNT:",
            analyses.length
        );

        // ----------------------------------------------------
        // Render saved conversation
        // ----------------------------------------------------

        renderConversationMessages(
            messages,
            analyses
        );

    }
    catch (error) {

        console.error(
            "Failed to load conversation:",
            error
        );

        showConversationLoadError(
            error.message
        );

    }

}


// ============================================================
// RENDER SAVED MESSAGES
//
// Each successful assistant response can have:
// 1. Dashboard button
// 2. PDF report button
//
// Dashboard is conversation-level, so only one dashboard
// button is shown for the selected conversation.
// ============================================================

function renderConversationMessages(
    messages,
    analyses = []
) {

    chatMessages.innerHTML = "";

    // --------------------------------------------------------
    // No messages
    // --------------------------------------------------------

    if (
        !messages ||
        messages.length === 0
    ) {

        showWelcomeMessage();

        return;

    }

    // --------------------------------------------------------
    // Reports are stored separately from messages.
    // Match them to successful assistant responses
    // in creation order.
    // --------------------------------------------------------

    let analysisIndex = 0;

    let dashboardAdded = false;

    // --------------------------------------------------------
    // Render messages in original order
    // --------------------------------------------------------

    messages.forEach(
        message => {

            if (!message) {
                return;
            }

            console.log(
                "Rendering saved message:",
                message.role,
                message.content
            );

            // =================================================
            // USER MESSAGE
            // =================================================

            if (
                message.role === "user"
            ) {

                addUserMessage(
                    message.content,
                    false
                );

                return;

            }

            // =================================================
            // ASSISTANT MESSAGE
            // =================================================

            if (
                message.role === "assistant"
            ) {

                addAssistantMessage(
                    message.content,
                    false
                );

                // ------------------------------------------------
                // Get exact assistant DOM element
                // ------------------------------------------------

                const assistantMessages =
                    chatMessages.querySelectorAll(
                        ".message.assistant"
                    );

                const currentAssistantMessage =
                    assistantMessages[
                        assistantMessages.length - 1
                    ];

                // ------------------------------------------------
                // Detect failed/error responses
                // ------------------------------------------------

                const content =
                    String(
                        message.content || ""
                    ).trim();

                const isErrorMessage =
                    content.startsWith("Error:") ||
                    content.includes(
                        "Gemini is temporarily unavailable"
                    ) ||
                    content.includes(
                        "Quota has been exceeded"
                    ) ||
                    content.includes(
                        "API quota has been exceeded"
                    ) ||
                    content.includes(
                        "Week 10 analysis pipeline failed"
                    ) ||
                    content.includes(
                        "Unable to load conversation"
                    );

                // ------------------------------------------------
                // Add dashboard button once
                // ------------------------------------------------

                if (
                    !isErrorMessage &&
                    !dashboardAdded &&
                    currentAssistantMessage
                ) {

                    addDashboardButton(
                        false,
                        currentAssistantMessage
                    );

                    dashboardAdded =
                        true;

                }

                // ------------------------------------------------
                // Add PDF report
                // ------------------------------------------------

                if (
                    !isErrorMessage &&
                    currentAssistantMessage &&
                    analysisIndex < analyses.length
                ) {

                    const analysis =
                        analyses[
                            analysisIndex
                        ];

                    if (
                        analysis &&
                        analysis.analysis_id &&
                        analysis.report_path
                    ) {

                        addReportButton(
                            analysis.analysis_id,
                            false,
                            currentAssistantMessage
                        );

                        analysisIndex++;

                    }

                }

            }

        }
    );

    scrollToBottom();

}


// ============================================================
// SHOW WELCOME MESSAGE
// ============================================================

function showWelcomeMessage() {

    chatMessages.innerHTML = `
        <div class="welcome">

            <div class="welcome-icon">
                ✦
            </div>

            <h1>
                AI BI Analyst
            </h1>

            <p>
                Ask business questions and get
                data-driven insights from your
                BI analytics pipeline.
            </p>

            <div class="example-questions">

                <button
                    class="example-question"
                    type="button"
                    data-question="What was the biggest revenue spike?"
                >
                    What was the biggest revenue spike?
                </button>

                <button
                    class="example-question"
                    type="button"
                    data-question="Show me the top 10 services by revenue."
                >
                    Show me the top 10 services by revenue.
                </button>

                <button
                    class="example-question"
                    type="button"
                    data-question="Which service contributed the most revenue?"
                >
                    Which service contributed the most revenue?
                </button>

            </div>

        </div>
    `;

    attachExampleQuestionEvents();

}


// ============================================================
// ADD USER MESSAGE
// ============================================================

function addUserMessage(
    content,
    shouldScroll = true
) {

    const message =
        document.createElement(
            "div"
        );

    message.className =
        "message user";

    const cleanContent =
        normalizeMessageText(
            content
        );

    message.innerHTML = `
        <div class="message-content">
            ${escapeHtml(cleanContent)}
        </div>
    `;

    chatMessages.appendChild(
        message
    );

    if (shouldScroll) {
        scrollToBottom();
    }

}


// ============================================================
// ADD ASSISTANT MESSAGE
// ============================================================

function addAssistantMessage(
    content,
    shouldScroll = true
) {

    const message =
        document.createElement(
            "div"
        );

    message.className =
        "message assistant";

    message.innerHTML = `
        <div class="message-content">
            ${formatAssistantText(content)}
        </div>
    `;

    chatMessages.appendChild(
        message
    );

    if (shouldScroll) {
        scrollToBottom();
    }

}


// ============================================================
// SEND CHAT MESSAGE
// ============================================================

chatForm.addEventListener(
    "submit",
    async event => {

        event.preventDefault();

        const question =
            questionInput.value.trim();

        if (!question) {
            return;
        }

        await sendQuestion(
            question
        );

    }
);


// ============================================================
// SEND QUESTION
// ============================================================

async function sendQuestion(
    question
) {

    if (!question) {
        return;
    }

    // --------------------------------------------------------
    // Disable input
    // --------------------------------------------------------

    setLoading(
        true
    );

    // --------------------------------------------------------
    // Add user message immediately
    // --------------------------------------------------------

    addUserMessage(
        question
    );

    // --------------------------------------------------------
    // Clear input
    // --------------------------------------------------------

    questionInput.value = "";

    resetTextareaHeight();

    try {

        // ----------------------------------------------------
        // Send request
        // ----------------------------------------------------

        const response =
            await fetch(
                `${API_BASE_URL}/api/chat`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        question:
                            question,

                        conversation_id:
                            conversationId

                    })
                }
            );

        const data =
            await response.json();

        // ----------------------------------------------------
        // Handle API error
        // ----------------------------------------------------

        if (!response.ok) {

            const errorMessage =
                data.detail ||
                data.message ||
                "An error occurred.";

            throw new Error(
                errorMessage
            );

        }

        // ----------------------------------------------------
        // Save conversation ID
        // ----------------------------------------------------

        if (
            data.conversation_id
        ) {

            const wasNewConversation =
                conversationId === null;

            conversationId =
                data.conversation_id;

            // ------------------------------------------------
            // Add conversation to sidebar
            // ------------------------------------------------

            if (
                wasNewConversation
            ) {

                addOrUpdateConversation(
                    data.conversation ||
                    {
                        conversation_id:
                            data.conversation_id,

                        title:
                            question
                    },
                    true
                );

            }
            else {

                addOrUpdateConversation(
                    data.conversation ||
                    {
                        conversation_id:
                            data.conversation_id
                    }
                );

            }

        }

        // ----------------------------------------------------
        // Assistant answer
        // ----------------------------------------------------

        const answer =
            data.answer ||
            data.message ||
            "No answer was returned.";

        addAssistantMessage(
            answer
        );

        // ----------------------------------------------------
        // Add dashboard button
        //
        // Dashboard is conversation-level, therefore
        // only one button is added.
        // ----------------------------------------------------

        addDashboardButton();

        // ----------------------------------------------------
        // Add PDF report button
        // ----------------------------------------------------

        if (
            data.analysis_id
        ) {

            addReportButton(
                data.analysis_id
            );

        }

    }
    catch (error) {

        console.error(
            "Chat error:",
            error
        );

        addAssistantMessage(
            `Error: ${error.message}`
        );

    }
    finally {

        setLoading(
            false
        );

    }

}


// ============================================================
// ADD OR UPDATE CONVERSATION
// ============================================================

function addOrUpdateConversation(
    conversation,
    prepend = false
) {

    if (!conversation) {
        return;
    }

    const id =
        conversation.conversation_id;

    if (!id) {
        return;
    }

    let item =
        document.querySelector(
            `[data-conversation-id="${id}"]`
        );

    // --------------------------------------------------------
    // Create if it does not exist
    // --------------------------------------------------------

    if (!item) {

        item =
            addConversation(
                conversation,
                prepend
            );

    }

    // --------------------------------------------------------
    // Update title
    // --------------------------------------------------------

    if (item) {

        const title =
            conversation.title ||
            "New BI Analysis";

        const titleElement =
            item.querySelector(
                ".conversation-title"
            );

        if (titleElement) {

            titleElement.textContent =
                title;

        }

    }

    // --------------------------------------------------------
    // Active state
    // --------------------------------------------------------

    document
        .querySelectorAll(
            ".conversation-item"
        )
        .forEach(
            element => {

                element.classList.remove(
                    "active"
                );

            }
        );

    if (item) {

        item.classList.add(
            "active"
        );

    }

}


// ============================================================
// ADD REPORT BUTTON
// ============================================================

function addReportButton(
    analysisId,
    shouldScroll = true,
    afterElement = null
) {

    if (!analysisId) {
        return;
    }

    // --------------------------------------------------------
    // Prevent duplicate report buttons
    // --------------------------------------------------------

    const existing =
        document.querySelector(
            `[data-analysis-id="${analysisId}"]`
        );

    if (existing) {
        return;
    }

    // --------------------------------------------------------
    // Wrapper
    // --------------------------------------------------------

    const wrapper =
        document.createElement(
            "div"
        );

    wrapper.className =
        "report-action";

    wrapper.dataset.analysisId =
        analysisId;

    // --------------------------------------------------------
    // Button
    // --------------------------------------------------------

    const button =
        document.createElement(
            "button"
        );

    button.className =
        "report-button";

    button.type =
        "button";

    button.textContent =
        "📄 View PDF Report";

    button.addEventListener(
        "click",
        () => {

            const reportUrl =
                `${API_BASE_URL}/api/reports/${encodeURIComponent(analysisId)}`;

            window.open(
                reportUrl,
                "_blank"
            );

        }
    );

    wrapper.appendChild(
        button
    );

    // --------------------------------------------------------
    // Insert after assistant response
    // --------------------------------------------------------

    if (
        afterElement &&
        afterElement.parentNode === chatMessages
    ) {

        chatMessages.insertBefore(
            wrapper,
            afterElement.nextSibling
        );

    }
    else {

        chatMessages.appendChild(
            wrapper
        );

    }

    if (shouldScroll) {
        scrollToBottom();
    }

}


// ============================================================
// ADD DASHBOARD BUTTON
// ============================================================

function addDashboardButton(
    shouldScroll = true,
    afterElement = null
) {

    if (!conversationId) {
        return;
    }

    // --------------------------------------------------------
    // Prevent duplicate dashboard button
    // --------------------------------------------------------

    const existing =
        document.querySelector(
            ".dashboard-action"
        );

    if (existing) {
        return;
    }

    // --------------------------------------------------------
    // Wrapper
    // --------------------------------------------------------

    const wrapper =
        document.createElement(
            "div"
        );

    wrapper.className =
        "dashboard-action";

    // --------------------------------------------------------
    // Button
    // --------------------------------------------------------

    const button =
        document.createElement(
            "button"
        );

    button.type =
        "button";

    button.className =
        "dashboard-button";

    button.innerHTML = `
        <span class="dashboard-button-icon">
            📊
        </span>

        <span class="dashboard-button-text">
            Open Dashboard
        </span>

        <span class="dashboard-button-arrow">
            ↗
        </span>
    `;

    button.addEventListener(
        "click",
        () => {

            openConversationDashboard();

        }
    );

    wrapper.appendChild(
        button
    );

    // --------------------------------------------------------
    // Insert after assistant response
    // --------------------------------------------------------

    if (
        afterElement &&
        afterElement.parentNode === chatMessages
    ) {

        chatMessages.insertBefore(
            wrapper,
            afterElement.nextSibling
        );

    }
    else {

        chatMessages.appendChild(
            wrapper
        );

    }

    if (shouldScroll) {
        scrollToBottom();
    }

}


// ============================================================
// NEW CHAT
// ============================================================

newChatButton.addEventListener(
    "click",
    () => {

        createNewChat();

    }
);


// ============================================================
// CREATE NEW CHAT
// ============================================================

function createNewChat() {

    console.log(
        "NEW CHAT: starting fresh conversation"
    );

    // --------------------------------------------------------
    // Forget current conversation
    // --------------------------------------------------------

    conversationId =
        null;

    // --------------------------------------------------------
    // Remove active sidebar state
    // --------------------------------------------------------

    document
        .querySelectorAll(
            ".conversation-item"
        )
        .forEach(
            element => {

                element.classList.remove(
                    "active"
                );

            }
        );

    // --------------------------------------------------------
    // Reset chat area
    // --------------------------------------------------------

    showWelcomeMessage();

    // --------------------------------------------------------
    // Reset input
    // --------------------------------------------------------

    questionInput.value = "";

    resetTextareaHeight();

    // --------------------------------------------------------
    // Focus input
    // --------------------------------------------------------

    questionInput.focus();

    console.log(
        "NEW CHAT: ready for first message"
    );

}


// ============================================================
// CONNECTION STATUS
// ============================================================

function setConnectionStatus(
    state,
    text
) {

    if (!connectionStatus) {
        return;
    }

    connectionStatus.innerHTML = `
        <span class="connection-dot"></span>
        <span>${escapeHtml(text)}</span>
    `;

    connectionStatus.classList.remove(
        "connected",
        "loading",
        "error"
    );

    connectionStatus.classList.add(
        state
    );

}


// ============================================================
// CONVERSATION LOADING
// ============================================================

function showConversationLoading() {

    chatMessages.innerHTML = `
        <div class="loading-message">

            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>

            <span>
                Loading conversation...
            </span>

        </div>
    `;

}


// ============================================================
// CONVERSATION LOAD ERROR
// ============================================================

function showConversationLoadError(
    errorMessage = ""
) {

    chatMessages.innerHTML = `
        <div class="message assistant">

            <div class="message-content">

                <strong>
                    Unable to load conversation
                </strong>

                <br><br>

                ${escapeHtml(
                    errorMessage ||
                    "Please try again."
                )}

            </div>

        </div>
    `;

}


// ============================================================
// CONVERSATION LIST ERROR
// ============================================================

function showConversationError() {

    conversationList.innerHTML = `
        <div class="empty-conversations">
            Unable to load conversations.
        </div>
    `;

}


// ============================================================
// EMPTY CONVERSATIONS
// ============================================================

function showEmptyConversations() {

    conversationList.innerHTML = `
        <div class="empty-conversations">
            No conversations yet.
        </div>
    `;

}


// ============================================================
// LOADING STATE
// ============================================================

function setLoading(
    loading
) {

    if (!sendButton) {
        return;
    }

    sendButton.disabled =
        loading;

    questionInput.disabled =
        loading;

    if (sendText) {

        sendText.textContent =
            loading
                ? "Analyzing..."
                : "Send";

    }

    if (loadingText) {

        loadingText.classList.toggle(
            "hidden",
            !loading
        );

    }

}


// ============================================================
// TEXTAREA
// ============================================================

function setupTextarea() {

    if (!questionInput) {
        return;
    }

    questionInput.addEventListener(
        "input",
        () => {

            questionInput.style.height =
                "auto";

            questionInput.style.height =
                `${questionInput.scrollHeight}px`;

        }
    );

    questionInput.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                chatForm.requestSubmit();

            }

        }
    );

}


// ============================================================
// RESET TEXTAREA HEIGHT
// ============================================================

function resetTextareaHeight() {

    if (!questionInput) {
        return;
    }

    questionInput.style.height =
        "auto";

}


// ============================================================
// EXAMPLE QUESTIONS
// ============================================================

function attachExampleQuestionEvents() {

    const buttons =
        document.querySelectorAll(
            ".example-question"
        );

    buttons.forEach(
        button => {

            if (
                button.dataset.listenerAttached === "true"
            ) {

                return;

            }

            button.dataset.listenerAttached =
                "true";

            button.addEventListener(
                "click",
                () => {

                    const question =
                        button.dataset.question;

                    if (!question) {
                        return;
                    }

                    questionInput.value =
                        question;

                    chatForm.requestSubmit();

                }
            );

        }
    );

}


// ============================================================
// SCROLL CHAT TO BOTTOM
// ============================================================

function scrollToBottom() {

    if (!chatMessages) {
        return;
    }

    chatMessages.scrollTop =
        chatMessages.scrollHeight;

}


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHtml(
    text
) {

    const div =
        document.createElement(
            "div"
        );

    div.textContent =
        text ?? "";

    return div.innerHTML;

}


// ============================================================
// NORMALIZE MESSAGE TEXT
// ============================================================

function normalizeMessageText(
    text
) {

    if (!text) {
        return "";
    }

    return String(text)

        // ----------------------------------------------------
        // Normalize Windows line endings
        // ----------------------------------------------------

        .replace(
            /\r\n/g,
            "\n"
        )

        .replace(
            /\r/g,
            "\n"
        )

        // ----------------------------------------------------
        // Remove tabs
        // ----------------------------------------------------

        .replace(
            /\t+/g,
            " "
        )

        // ----------------------------------------------------
        // Remove Dashboard section generated by backend
        //
        // The dashboard is now rendered as a real UI button.
        // ----------------------------------------------------

        .replace(
            /---\s*\n+###\s*\s*Interactive Dashboard[\s\S]*?(?=\n---|\s*$)/i,
            ""
        )

        // ----------------------------------------------------
        // Remove leading/trailing spaces from every line
        // ----------------------------------------------------

        .split("\n")
        .map(
            line => line.trim()
        )
        .join("\n")

        // ----------------------------------------------------
        // Prevent too many empty lines
        // ----------------------------------------------------

        .replace(
            /\n{3,}/g,
            "\n\n"
        )

        // ----------------------------------------------------
        // Remove whitespace at beginning/end
        // ----------------------------------------------------

        .trim();

}


// ============================================================
// FORMAT ASSISTANT TEXT
// ============================================================

function formatAssistantText(
    text
) {

    if (!text) {
        return "";
    }

    // --------------------------------------------------------
    // Clean unwanted indentation and dashboard section
    // --------------------------------------------------------

    let formatted =
        normalizeMessageText(
            text
        );

    // --------------------------------------------------------
    // Escape HTML
    // --------------------------------------------------------

    formatted =
        escapeHtml(
            formatted
        );

    // --------------------------------------------------------
    // Bold
    // --------------------------------------------------------

    formatted =
        formatted.replace(
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
        );

    // --------------------------------------------------------
    // Headings
    // --------------------------------------------------------

    formatted =
        formatted.replace(
            /^### (.*?)$/gm,
            "<h4>$1</h4>"
        );

    formatted =
        formatted.replace(
            /^## (.*?)$/gm,
            "<h3>$1</h3>"
        );

    formatted =
        formatted.replace(
            /^# (.*?)$/gm,
            "<h2>$1</h2>"
        );

    // --------------------------------------------------------
    // Horizontal rule
    // --------------------------------------------------------

    formatted =
        formatted.replace(
            /^---+$/gm,
            "<hr>"
        );

    // --------------------------------------------------------
    // Bullet points
    // --------------------------------------------------------

    formatted =
        formatted.replace(
            /^[-*] (.*?)$/gm,
            "• $1"
        );

    // --------------------------------------------------------
    // Line breaks
    // --------------------------------------------------------

    formatted =
        formatted.replace(
            /\n/g,
            "<br>"
        );

    return formatted;

}


// ============================================================
// OPEN CONVERSATION DASHBOARD
// ============================================================

function openConversationDashboard() {

    if (!conversationId) {
        return;
    }

    const dashboardUrl =
        `http://127.0.0.1:8501/?conversation_id=${encodeURIComponent(
            conversationId
        )}`;

    window.open(
        dashboardUrl,
        "_blank"
    );

}