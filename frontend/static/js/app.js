// AI 资讯聚合 - 前端应用

const API_BASE = '/api';

class NewsAggregator {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 20;
        this.totalPages = 1;
        this.filters = {
            category: '',
            source: '',
            status: '',
            search: ''
        };
        this.categories = [];
        this.sources = [];
        this.currentArticle = null;

        this.init();
    }

    async init() {
        this.bindEvents();
        await this.loadFilters();
        await this.loadArticles();
    }

    bindEvents() {
        // 搜索
        document.getElementById('searchInput').addEventListener('input', debounce((e) => {
            this.filters.search = e.target.value;
            this.currentPage = 1;
            this.loadArticles();
        }, 500));

        // 分类筛选
        document.getElementById('categoryFilter').addEventListener('change', (e) => {
            this.filters.category = e.target.value;
            this.currentPage = 1;
            this.loadArticles();
        });

        // 来源筛选
        document.getElementById('sourceFilter').addEventListener('change', (e) => {
            this.filters.source = e.target.value;
            this.currentPage = 1;
            this.loadArticles();
        });

        // 状态标签筛选
        document.querySelectorAll('.status-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.status-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                this.filters.status = tab.dataset.status;
                this.currentPage = 1;
                this.loadArticles();
            });
        });

        // 分页
        document.getElementById('prevPage').addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.loadArticles();
            }
        });

        document.getElementById('nextPage').addEventListener('click', () => {
            if (this.currentPage < this.totalPages) {
                this.currentPage++;
                this.loadArticles();
            }
        });

        // 刷新按钮
        document.getElementById('refreshBtn').addEventListener('click', async () => {
            await this.fetchAllSources();
        });

        // 添加来源按钮
        document.getElementById('addSourceBtn').addEventListener('click', () => {
            this.openModal('addSourceModal');
        });

        // 添加来源表单
        document.getElementById('addSourceForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addSource();
        });

        // 模态框关闭按钮
        document.querySelectorAll('.modal-close, .modal-close-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.closeAllModals();
            });
        });

        // 点击背景关闭模态框
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeAllModals();
                }
            });
        });

        // ESC 键关闭模态框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }

    async loadFilters() {
        try {
            // 加载分类
            const categoriesRes = await fetch(`${API_BASE}/categories/`);
            this.categories = await categoriesRes.json();
            this.populateFilter('categoryFilter', this.categories);
            this.populateFilter('sourceCategory', this.categories, true);

            // 加载来源
            const sourcesRes = await fetch(`${API_BASE}/sources/`);
            this.sources = await sourcesRes.json();
            this.populateFilter('sourceFilter', this.sources);
        } catch (error) {
            console.error('加载筛选条件失败:', error);
        }
    }

    populateFilter(selectId, items, includeNone = false) {
        const select = document.getElementById(selectId);
        const firstOption = includeNone ? select.querySelector('option') : select.querySelector('option:first-child');
        select.innerHTML = '';
        if (firstOption) {
            select.appendChild(firstOption);
        }

        items.forEach(item => {
            const option = document.createElement('option');
            option.value = item.id;
            option.textContent = item.name;
            select.appendChild(option);
        });
    }

    async loadArticles() {
        this.showLoading(true);

        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                page_size: this.pageSize
            });

            if (this.filters.category) params.append('category_id', this.filters.category);
            if (this.filters.source) params.append('source_id', this.filters.source);
            if (this.filters.search) params.append('search', this.filters.search);

            if (this.filters.status === 'unread') {
                params.append('is_read', 'false');
            } else if (this.filters.status === 'read') {
                params.append('is_read', 'true');
            } else if (this.filters.status === 'bookmarked') {
                params.append('is_bookmarked', 'true');
            }

            const response = await fetch(`${API_BASE}/content/?${params}`);
            const data = await response.json();

            this.totalPages = Math.ceil(data.total / this.pageSize);
            this.renderArticles(data.items);
            this.updatePagination(data.total);

            // 更新状态标签计数
            this.updateStatusCounts();
        } catch (error) {
            console.error('加载文章失败:', error);
            this.showError('加载文章失败');
        }

        this.showLoading(false);
    }

    renderArticles(articles) {
        const list = document.getElementById('articlesList');
        const emptyState = document.getElementById('emptyState');

        if (!articles || articles.length === 0) {
            list.innerHTML = '';
            emptyState.classList.remove('hidden');
            document.getElementById('pagination').classList.add('hidden');
            return;
        }

        emptyState.classList.add('hidden');
        document.getElementById('pagination').classList.remove('hidden');

        list.innerHTML = articles.map(article => this.createArticleCard(article)).join('');

        // 绑定文章卡片事件
        list.querySelectorAll('.article-card').forEach(card => {
            const articleId = card.dataset.id;
            const article = articles.find(a => a.id === parseInt(articleId));

            card.addEventListener('click', (e) => {
                // 忽略操作按钮的点击
                if (e.target.closest('.article-actions')) return;
                this.openArticle(article);
            });

            // 标记已读按钮
            const readBtn = card.querySelector('.btn-read');
            if (readBtn) {
                readBtn.addEventListener('click', async () => {
                    await this.toggleReadStatus(articleId, article.is_read);
                });
            }

            // 收藏按钮
            const bookmarkBtn = card.querySelector('.btn-bookmark');
            if (bookmarkBtn) {
                bookmarkBtn.addEventListener('click', async () => {
                    await this.toggleBookmark(articleId);
                });
            }
        });
    }

    createArticleCard(article) {
        const category = this.categories.find(c => c.id === article.categories[0]?.id);
        const source = this.sources.find(s => s.id === article.rss_source_id);
        const date = this.formatDate(article.published_date);

        return `
            <article class="article-card ${!article.is_read ? 'unread' : ''} ${article.is_bookmarked ? 'bookmarked' : ''}" data-id="${article.id}">
                <div class="article-header">
                    <div class="article-meta">
                        ${source ? `<span class="article-source">${source.name}</span>` : ''}
                        ${category ? `<span class="article-category" style="background-color: ${category.color}">${category.name}</span>` : ''}
                        <span class="article-date">${date}</span>
                    </div>
                    <div class="article-actions">
                        <button class="icon-btn btn-read ${article.is_read ? 'active' : ''}" title="${article.is_read ? '标记为未读' : '标记为已读'}">
                            <svg viewBox="0 0 24 24" fill="${article.is_read ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2">
                                <path d="M5 13l4 4L19 7"/>
                            </svg>
                        </button>
                        <button class="icon-btn btn-bookmark ${article.is_bookmarked ? 'bookmarked' : ''}" title="${article.is_bookmarked ? '取消收藏' : '添加收藏'}">
                            <svg viewBox="0 0 24 24" fill="${article.is_bookmarked ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2">
                                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                            </svg>
                        </button>
                    </div>
                </div>
                <h3 class="article-title ${!article.is_read ? 'unread' : ''}">${this.escapeHtml(article.title)}</h3>
                <p class="article-summary">${this.escapeHtml(article.summary || '暂无摘要')}</p>
                <div class="article-footer">
                    <a href="${this.escapeHtml(article.link)}" target="_blank" class="article-link">阅读原文 &rarr;</a>
                </div>
            </article>
        `;
    }

    openArticle(article) {
        this.currentArticle = article;

        // 标记为已读
        if (!article.is_read) {
            this.toggleReadStatus(article.id, false);
        }

        const modalContent = document.getElementById('modalContent');
        const category = this.categories.find(c => c.id === article.categories[0]?.id);
        const source = this.sources.find(s => s.id === article.rss_source_id);
        const date = this.formatDate(article.published_date);

        modalContent.innerHTML = `
            <div class="article-meta">
                ${source ? `<span class="article-source">${source.name}</span>` : ''}
                ${category ? `<span class="article-category" style="background-color: ${category.color}">${category.name}</span>` : ''}
                <span class="article-date">${date}</span>
            </div>
            <h2>${this.escapeHtml(article.title)}</h2>
            ${article.author ? `<p class="article-author">作者: ${this.escapeHtml(article.author)}</p>` : ''}
            ${article.image_url ? `<img src="${this.escapeHtml(article.image_url)}" alt="" class="article-image" onerror="this.style.display='none'">` : ''}

            ${article.summary ? `
                <div class="article-summary-box">
                    <h4>摘要</h4>
                    <p class="article-summary-full">${this.escapeHtml(article.summary)}</p>
                </div>
            ` : ''}

            <div class="article-footer">
                <a href="${this.escapeHtml(article.link)}" target="_blank" class="btn btn-primary">
                    阅读原文 &rarr;
                </a>
                <button class="btn btn-outline btn-bookmark-modal ${article.is_bookmarked ? 'active' : ''}">
                    ${article.is_bookmarked ? '取消收藏' : '添加收藏'}
                </button>
            </div>
        `;

        // 绑定模态框事件
        modalContent.querySelector('.btn-bookmark-modal')?.addEventListener('click', async () => {
            await this.toggleBookmark(article.id);
            // 更新按钮文本
            const btn = modalContent.querySelector('.btn-bookmark-modal');
            if (btn) {
                btn.textContent = this.currentArticle.is_bookmarked ? '取消收藏' : '添加收藏';
            }
        });

        this.openModal('articleModal');
    }

    async toggleReadStatus(articleId, isRead) {
        const endpoint = isRead ? '/mark-unread' : '/mark-read';
        try {
            await fetch(`${API_BASE}/content/${articleId}${endpoint}`, { method: 'POST' });
            await this.loadArticles(); // 刷新 UI
        } catch (error) {
            console.error('切换阅读状态失败:', error);
        }
    }

    async toggleBookmark(articleId) {
        try {
            await fetch(`${API_BASE}/content/${articleId}/bookmark`, { method: 'POST' });
            await this.loadArticles(); // 刷新 UI
        } catch (error) {
            console.error('切换收藏失败:', error);
        }
    }

    async fetchAllSources() {
        const btn = document.getElementById('refreshBtn');
        btn.disabled = true;

        try {
            await fetch(`${API_BASE}/content/fetch-all`, { method: 'POST' });
            setTimeout(() => this.loadArticles(), 2000); // 等待抓取完成
        } catch (error) {
            console.error('抓取文章失败:', error);
            this.showError('抓取文章失败');
        }

        btn.disabled = false;
    }

    async addSource() {
        const form = document.getElementById('addSourceForm');
        const formData = new FormData(form);

        const data = {
            name: formData.get('name'),
            url: formData.get('url'),
            category_id: formData.get('category_id') || null,
            description: formData.get('description') || null
        };

        try {
            const response = await fetch(`${API_BASE}/sources/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                this.closeAllModals();
                form.reset();
                await this.loadFilters(); // 刷新筛选条件
                await this.fetchAllSources(); // 抓取新文章
            } else {
                const error = await response.json();
                this.showError(error.detail || '添加来源失败');
            }
        } catch (error) {
            console.error('添加来源失败:', error);
            this.showError('添加来源失败');
        }
    }

    async updateStatusCounts() {
        try {
            const baseParams = new URLSearchParams();
            if (this.filters.category) baseParams.append('category_id', this.filters.category);
            if (this.filters.source) baseParams.append('source_id', this.filters.source);
            if (this.filters.search) baseParams.append('search', this.filters.search);
            baseParams.append('page_size', '1');

            // Fetch counts in parallel
            const [allRes, unreadRes, readRes, bookmarkedRes] = await Promise.all([
                fetch(`${API_BASE}/content/?${new URLSearchParams(baseParams)}`),
                fetch(`${API_BASE}/content/?${new URLSearchParams([...baseParams, ['is_read', 'false']])}`),
                fetch(`${API_BASE}/content/?${new URLSearchParams([...baseParams, ['is_read', 'true']])}`),
                fetch(`${API_BASE}/content/?${new URLSearchParams([...baseParams, ['is_bookmarked', 'true']])}`),
            ]);

            const [allData, unreadData, readData, bookmarkedData] = await Promise.all([
                allRes.json(), unreadRes.json(), readRes.json(), bookmarkedRes.json()
            ]);

            const setCount = (id, count) => {
                const el = document.getElementById(id);
                if (el) el.textContent = count > 0 ? count : '';
            };

            setCount('countAll', allData.total);
            setCount('countUnread', unreadData.total);
            setCount('countRead', readData.total);
            setCount('countBookmarked', bookmarkedData.total);
        } catch (error) {
            console.error('更新状态计数失败:', error);
        }
    }

    updatePagination(total) {
        document.getElementById('pageInfo').textContent =
            `第 ${this.currentPage} / ${this.totalPages} 页 (共 ${total} 篇)`;
        document.getElementById('prevPage').disabled = this.currentPage <= 1;
        document.getElementById('nextPage').disabled = this.currentPage >= this.totalPages;
    }

    openModal(modalId) {
        document.getElementById(modalId).classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    closeAllModals() {
        document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden'));
        document.body.style.overflow = '';
    }

    showLoading(show) {
        document.getElementById('loading').classList.toggle('hidden', !show);
        document.getElementById('articlesList').classList.toggle('hidden', show);
        if (show) {
            document.getElementById('emptyState').classList.add('hidden');
        }
    }

    showError(message) {
        alert(message);
    }

    formatDate(dateStr) {
        if (!dateStr) return '未知日期';
        const date = new Date(dateStr);
        const now = new Date();
        const diff = now - date;

        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return '刚刚';
        if (minutes < 60) return `${minutes} 分钟前`;
        if (hours < 24) return `${hours} 小时前`;
        if (days < 7) return `${days} 天前`;

        return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', year: 'numeric' });
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 工具函数: 防抖
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// DOM 加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new NewsAggregator();
});
