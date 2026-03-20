/**
 * Legal Module - 隐私政策、用户协议、数据来源声明
 * 法务模块 - 法律声明和条款
 */

// 应用版本号
const APP_VERSION = 'v1.3.0';

// 法律声明内容
const LEGAL_CONTENT = {
  privacy: {
    title: '隐私政策',
    icon: '🔒',
    content: `
<div class="legal-section">
<h3>一、引言</h3>
<p>「Prism - 棱镜情报」（以下简称"本产品"）是一款 AI 驱动的开源情报聚合工具，由独立开发者运营。<strong>本产品仅提供工具使用权，所有 AI 功能均由用户自备 API Key 直连调用，我们不代理、不存储、不触碰您的 API 密钥和 AI 请求内容。</strong></p>
<p>我们深知个人信息保护的重要性，并严格遵守《中华人民共和国个人信息保护法》（PIPL）、《数据安全法》及《网络安全法》等相关法律法规。本政策旨在向您说明我们如何收集、使用和保护信息。</p>
</div>

<div class="legal-section">
<h3>二、服务分层与信息收集</h3>
<p>本产品采用分层服务模式，不同服务层级收集的信息有所不同：</p>

<h4>2.1 免费服务（无需注册）</h4>
<p>使用免费服务时，<strong>我们不要求您注册账户</strong>，也不收集姓名、手机号、邮箱等个人身份信息。</p>
<p>我们可能在您使用过程中涉及以下非个人信息：</p>
<ul>
<li><strong>身份凭证（JWT）与缓存</strong>：为实现设备互通和频率控制，系统会在您的浏览器本地存储中写入一个签名的数字凭证（JWT）。此凭证仅包含设备标识和会话有效期，不含任何个人隐私数据。此外，生成的报告摘要也会缓存在本地以提升加载速度。</li>
<li><strong>用户配置数据</strong>：您在设置中填写的 API Key、数据源配置、Prompt 模板等<strong>均存储在您的浏览器本地</strong>，不会上传至我们的服务器。</li>
</ul>

<h4>2.2 付费服务（需注册账户）</h4>
<p>使用付费服务时，我们需要您注册账户，届时将收集以下信息：</p>
<ul>
<li><strong>注册信息</strong>：邮箱地址、密码（加密存储）、昵称（可选）</li>
<li><strong>OAuth 授权信息</strong>：如您选择第三方登录，我们将获取该平台的公开信息</li>
<li><strong>订阅信息</strong>：激活码/兑换码、订阅状态、订阅有效期、功能权限</li>
<li><strong>使用统计</strong>：工具使用次数、功能调用统计（用于功能限流和订阅管理，<strong>不包含您处理的具体内容</strong>）</li>
</ul>

<h4>2.3 邀请关系</h4>
<p>如您通过邀请码/邀请链接注册或激活订阅，我们会记录邀请关系（邀请人与被邀请人），用于发放邀请奖励和优惠。此信息仅用于邀请激励计划，不会用于其他目的。</p>

<h4>2.4 我们不收集的信息</h4>
<ul>
<li>❌ 不收集真实姓名、身份证号、手机号（除非您主动提供）</li>
<li>❌ 不收集银行卡等支付信息（支付由第三方支付平台处理）</li>
<li>❌ <strong>不存储您的 API Key</strong>（存储在您的浏览器本地）</li>
<li>❌ <strong>不代理您的 AI 请求</strong>（您直连 AI 服务商）</li>
<li>❌ <strong>不获取您发送给 AI 的内容</strong>（情报内容、Prompt 等）</li>
<li>❌ 不使用 Cookie 进行跨站追踪</li>
<li>❌ 不进行用户画像或行为分析广告投放</li>
</ul>
</div>

<div class="legal-section">
<h3>三、AI 功能与数据流向说明</h3>

<h4>3.1 API Key 管理</h4>
<p>本产品的 AI 功能需要您自备 API Key。您的 API Key 相关说明：</p>
<ul>
<li><strong>存储位置</strong>：您的浏览器本地存储</li>
<li><strong>传输方式</strong>：仅在使用 AI 功能时，由您的浏览器<strong>直接发送</strong>至您选择的 AI 服务商</li>
<li><strong>我们的角色</strong>：我们不代理、不中转、不存储您的 API Key 和请求内容</li>
</ul>

<h4>3.2 AI 请求流向</h4>
<pre style="background: var(--bg-tertiary); padding: 12px; border-radius: 8px; font-size: 13px;">
您的浏览器 → 棱镜工具前端 → 您选择的 AI 服务商
                    ↑
               我们不参与此环节
</pre>

<h4>3.3 您需要注意</h4>
<ul>
<li>请妥善保管您的 API Key，不要分享给他人</li>
<li>您与 AI 服务商之间的数据传输遵循该服务商的隐私政策</li>
<li>AI 生成的内容由您选择的模型服务商处理，我们不对其负责</li>
</ul>
</div>

<div class="legal-section">
<h3>四、数据存储与保留</h3>

<h4>4.1 数据存储位置</h4>
<table style="width: 100%; border-collapse: collapse; font-size: 13px;">
<tr><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">数据类型</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">存储位置</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">说明</th></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">用户 API Key</td><td style="padding: 8px; border: 1px solid var(--border);">浏览器本地</td><td style="padding: 8px; border: 1px solid var(--border);">不上传服务器</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">数据源配置</td><td style="padding: 8px; border: 1px solid var(--border);">浏览器本地</td><td style="padding: 8px; border: 1px solid var(--border);">不上传服务器</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">Prompt 模板</td><td style="padding: 8px; border: 1px solid var(--border);">浏览器本地</td><td style="padding: 8px; border: 1px solid var(--border);">不上传服务器</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">生成的报告</td><td style="padding: 8px; border: 1px solid var(--border);">浏览器本地</td><td style="padding: 8px; border: 1px solid var(--border);">不上传服务器</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">免费用户凭证</td><td style="padding: 8px; border: 1px solid var(--border);">浏览器本地</td><td style="padding: 8px; border: 1px solid var(--border);">JWT 会话</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">付费用户账户</td><td style="padding: 8px; border: 1px solid var(--border);">我们的服务器</td><td style="padding: 8px; border: 1px solid var(--border);">邮箱、订阅状态</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">付费用户报告（可选）</td><td style="padding: 8px; border: 1px solid var(--border);">我们的服务器</td><td style="padding: 8px; border: 1px solid var(--border);">30 天自动清理</td></tr>
</table>

<h4>4.2 数据保留期限</h4>
<table style="width: 100%; border-collapse: collapse; font-size: 13px;">
<tr><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">数据类型</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">保留期限</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">说明</th></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">用户账户信息</td><td style="padding: 8px; border: 1px solid var(--border);">账户存续期间</td><td style="padding: 8px; border: 1px solid var(--border);">注销后立即删除</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">订阅/激活记录</td><td style="padding: 8px; border: 1px solid var(--border);">账户存续期间</td><td style="padding: 8px; border: 1px solid var(--border);">用于续期和权益查询</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">云端保存的报告（可选）</td><td style="padding: 8px; border: 1px solid var(--border);">30 天</td><td style="padding: 8px; border: 1px solid var(--border);">自动清理过期报告</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">邀请关系记录</td><td style="padding: 8px; border: 1px solid var(--border);">账户存续期间</td><td style="padding: 8px; border: 1px solid var(--border);">用于邀请奖励发放</td></tr>
</table>

<h4>4.3 买断部署版</h4>
<p>如您购买买断部署版，所有数据存储在您自己的服务器，由您自行管理和保护。</p>
</div>

<div class="legal-section">
<h3>五、第三方服务</h3>
<p>本产品使用以下第三方服务，请注意其独立的隐私政策：</p>
<table style="width: 100%; border-collapse: collapse; font-size: 13px;">
<tr><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">服务商</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">用途</th></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">OpenAI / Google Gemini / xAI Grok / 其他</td><td style="padding: 8px; border: 1px solid var(--border);">AI 内容生成（用户自选，直连）</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">GitHub / Google（OAuth）</td><td style="padding: 8px; border: 1px solid var(--border);">第三方登录</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">数据源（Hacker News、36Kr 等）</td><td style="padding: 8px; border: 1px solid var(--border);">资讯聚合</td></tr>
</table>
<p><strong>重要说明</strong>：您的 AI 请求直接发送至您选择的模型服务商，不经过我们的服务器。请查阅该服务商的隐私政策了解其数据处理方式。</p>
</div>

<div class="legal-section">
<h3>六、AI 生成内容声明</h3>
<div style="background: rgba(124,92,252,0.1); border: 1px solid rgba(124,92,252,0.3); border-radius: 8px; padding: 16px; margin: 12px 0;">
<p style="margin: 0;">🤖 <strong>本产品使用 AI 技术对公开资讯进行摘要、翻译和分析。所有 AI 生成的内容均标注「AI 生成」标识，符合《人工智能生成合成内容标识管理办法》（2025 年 9 月 1 日起施行）的要求。</strong></p>
</div>
<p>AI 生成内容可能存在"幻觉"、不准确或过时的情况，仅供参考，不代表原文观点，不构成任何投资、法律或专业决策建议。用户应自行核实信息的准确性，并对基于本产品内容所做的任何决策承担全部责任。</p>
</div>

<div class="legal-section">
<h3>七、用户权利</h3>
<p>根据相关法律法规，您享有以下权利：</p>
<ul>
<li><strong>知情权</strong>：通过本政策了解信息处理规则</li>
<li><strong>访问权</strong>：可随时查看您的账户信息和订阅状态</li>
<li><strong>更正权</strong>：可更新您的账户信息</li>
<li><strong>删除权</strong>：可注销账户，我们将删除您的所有个人数据</li>
<li><strong>数据可携带权</strong>：可导出您的配置和报告数据</li>
<li><strong>撤回同意权</strong>：可随时停止使用本产品</li>
</ul>
<p>如需行使上述权利，请通过本政策底部的联系方式与我们联系。</p>
</div>

<div class="legal-section">
<h3>八、未成年人保护</h3>
<p>本产品不面向未满 14 周岁的未成年人。如果我们发现无意中处理了未成年人的个人信息，将立即采取删除措施。</p>
</div>

<div class="legal-section">
<h3>九、安全措施</h3>
<ul>
<li>全链路 HTTPS 加密传输</li>
<li>密码使用 bcrypt 加密存储，不存储明文密码</li>
<li>API Key 存储在用户浏览器本地，不上传服务器</li>
<li>用户数据定期自动清理，减少数据泄露风险</li>
<li>定期审查系统安全状态</li>
</ul>
</div>

<div class="legal-section">
<h3>十、政策更新</h3>
<p>我们可能不时更新本隐私政策。更新后的政策将在本页面发布，并更新"最后更新"日期。重大变更将通过产品内通知方式告知用户。</p>
</div>

<div class="legal-section">
<h3>十一、联系我们</h3>
<p>如果您对本隐私政策有任何疑问或建议，请通过以下方式联系：</p>
<ul>
<li>🔗 GitHub：<a href="https://github.com/mumuer1024/Prism" target="_blank">https://github.com/mumuer1024/Prism</a></li>
</ul>
<p style="color: var(--text-muted); font-size: 12px; margin-top: 16px;">最后更新：2026 年 3 月</p>
</div>
`
  },

  terms: {
    title: '用户服务协议',
    icon: '📋',
    content: `
<div class="legal-section">
<h3>一、服务范围</h3>
<p>「Prism - 棱镜情报」（以下简称"本产品"）是一款面向技术从业者和信息爱好者的 AI 情报聚合工具。本产品提供以下核心服务：</p>
<ul>
<li>聚合公开渠道（RSS 订阅、公开 API）的科技、AI、经济等领域资讯</li>
<li>使用 AI 技术对原文进行摘要提炼和中文翻译（需用户自备 API Key）</li>
<li>提供可定制的数据源配置和 Prompt 模板</li>
</ul>
</div>

<div class="legal-section">
<h3>二、AI 生成内容免责声明</h3>
<div style="background: rgba(255,107,107,0.1); border: 1px solid rgba(255,107,107,0.3); border-radius: 8px; padding: 16px; margin: 12px 0;">
<p style="margin: 0;">⚠️ <strong>本产品中标注「AI 生成」的内容由大语言模型自动生成。AI 生成内容可能存在"幻觉"、不准确或过时的情况。AI 生成内容不构成投资建议、法律意见或任何专业决策建议。用户应自行核实信息的准确性，并对基于本产品内容所做的任何决策承担全部责任。</strong></p>
</div>
</div>

<div class="legal-section">
<h3>三、知识产权</h3>

<h4>3.1 原文版权</h4>
<p>本产品聚合的所有原始文章、新闻报道的版权归其原始作者或出版方所有。本产品仅提供原文链接和 AI 生成的摘要转述，不对原文进行全文复制或再分发。</p>

<h4>3.2 AI 摘要</h4>
<p>AI 生成的摘要和翻译属于对原文的「转化性使用」（Transformative Use），包括语言转换、要点提炼和观点归纳。摘要内容均附有原文链接，方便用户查阅原文。</p>

<h4>3.3 产品本身</h4>
<p>本产品的源代码以开源形式发布于 GitHub：<a href="https://github.com/mumuer1024/Prism" target="_blank">https://github.com/mumuer1024/Prism</a></p>
</div>

<div class="legal-section">
<h3>四、用户行为规范</h3>
<p>使用本产品时，您同意不得：</p>
<ul>
<li>利用本产品进行任何违反中华人民共和国法律法规的行为</li>
<li>将 AI 生成的内容伪装为人工撰写的原创内容进行传播</li>
<li>通过技术手段大规模爬取本产品的数据</li>
<li>对本产品进行反向工程、破解或恶意攻击</li>
<li>利用本产品生成的内容进行造谣、传播虚假信息</li>
<li>将您的账户或激活码恶意分享给他人用于商业牟利</li>
</ul>
</div>

<div class="legal-section">
<h3>五、服务可用性与额度限制</h3>
<p>本产品作为独立极客项目，以"现状"（as-is）提供服务。为保障整体网络健康，我们对服务的功能使用实施<strong>合理使用限制</strong>。</p>

<h4>以下情况可能导致服务中断或账户限制：</h4>
<ul>
<li>超出您订阅层级的功能使用限制</li>
<li>短时间内发起的超高频异常请求</li>
<li>第三方服务（AI 模型服务商）的不可抗力中断</li>
<li>数据源（RSS 订阅等）的反爬拦截或结构变更</li>
</ul>

<p>对于正常的服务中断，我们不承担赔偿责任，但会以最高优先级抢修。</p>
</div>

<div class="legal-section">
<h3>六、API Key 安全责任</h3>
<p>本产品的 AI 功能需要您自备 API Key，您需自行承担以下责任：</p>
<ul>
<li>妥善保管您的 API Key，不得泄露给他人</li>
<li>定期检查 API Key 的使用情况，发现异常及时更换</li>
<li>因 API Key 泄露导致的损失由您自行承担</li>
<li>遵守您所使用的 AI 服务商的服务条款</li>
</ul>
</div>

<div class="legal-section">
<h3>七、免责声明</h3>
<ul>
<li>本产品不对 AI 生成内容的准确性、完整性或时效性做出任何明示或暗示的保证</li>
<li>用户基于本产品内容做出的任何投资、商业或个人决策，由用户自行承担风险与后果</li>
<li>对于因第三方服务（AI 服务商、数据源等）故障导致的服务中断，我们不承担责任</li>
<li>用户因未妥善保管 API Key 导致的损失，我们不承担责任</li>
</ul>
</div>

<div class="legal-section">
<h3>八、协议变更</h3>
<p>我们保留随时修改本协议的权利。修改后的协议将在本页面更新并注明最新日期。继续使用本产品即视为接受修改后的协议。重大变更将通过产品内通知方式告知。</p>
</div>

<div class="legal-section">
<h3>九、适用法律与争议解决</h3>
<p>本协议的订立、履行、解释及争议解决均适用中华人民共和国法律（不包括港澳台地区法律）。因本协议引发的任何争议，双方应首先友好协商解决；协商不成的，任何一方均可向本产品开发者所在地有管辖权的人民法院提起诉讼。</p>
<p style="color: var(--text-muted); font-size: 12px; margin-top: 16px;">最后更新：2026 年 3 月</p>
</div>
`
  },

  sources: {
    title: '数据来源声明',
    icon: '📡',
    content: `
<div class="legal-section">
<h3>一、数据来源概述</h3>
<p>「Prism - 棱镜情报」聚合来自以下公开渠道的信息，所有数据均来自各平台的公开前端接口或官方 API：</p>
</div>

<div class="legal-section">
<h3>二、数据源详情</h3>

<h4>2.1 科技前沿与开源趋势</h4>
<table style="width: 100%; border-collapse: collapse; font-size: 13px;">
<tr><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">数据源</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">获取方式</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">内容类型</th></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">Hacker News</td><td style="padding: 8px; border: 1px solid var(--border);">官方公开 API</td><td style="padding: 8px; border: 1px solid var(--border);">技术热点</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">GitHub Trending</td><td style="padding: 8px; border: 1px solid var(--border);">公开页面</td><td style="padding: 8px; border: 1px solid var(--border);">开源项目趋势</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">ArXiv</td><td style="padding: 8px; border: 1px solid var(--border);">官方 API</td><td style="padding: 8px; border: 1px solid var(--border);">学术论文</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">HN Blogs</td><td style="padding: 8px; border: 1px solid var(--border);">RSS 订阅</td><td style="padding: 8px; border: 1px solid var(--border);">技术博客</td></tr>
</table>

<h4>2.2 资本动向与宏观经济</h4>
<table style="width: 100%; border-collapse: collapse; font-size: 13px;">
<tr><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">数据源</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">获取方式</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">内容类型</th></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">36氪（36Kr）</td><td style="padding: 8px; border: 1px solid var(--border);">公开 RSS</td><td style="padding: 8px; border: 1px solid var(--border);">创投快讯</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">华尔街见闻</td><td style="padding: 8px; border: 1px solid var(--border);">公开 RSS</td><td style="padding: 8px; border: 1px solid var(--border);">宏观经济</td></tr>
</table>

<h4>2.3 产品与社区</h4>
<table style="width: 100%; border-collapse: collapse; font-size: 13px;">
<tr><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">数据源</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">获取方式</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">内容类型</th></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">Product Hunt</td><td style="padding: 8px; border: 1px solid var(--border);">官方 API</td><td style="padding: 8px; border: 1px solid var(--border);">新品发布</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">V2EX</td><td style="padding: 8px; border: 1px solid var(--border);">公开 RSS</td><td style="padding: 8px; border: 1px solid var(--border);">社区热议</td></tr>
</table>

<h4>2.4 社交与情绪</h4>
<table style="width: 100%; border-collapse: collapse; font-size: 13px;">
<tr><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">数据源</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">获取方式</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">内容类型</th></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">X (Twitter)</td><td style="padding: 8px; border: 1px solid var(--border);">用户自备 API Key</td><td style="padding: 8px; border: 1px solid var(--border);">社交情绪</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">小红书</td><td style="padding: 8px; border: 1px solid var(--border);">搜索链接指引</td><td style="padding: 8px; border: 1px solid var(--border);">消费趋势</td></tr>
</table>

<h4>2.5 扩展与机会</h4>
<table style="width: 100%; border-collapse: collapse; font-size: 13px;">
<tr><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">数据源</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">获取方式</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">内容类型</th></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">Chrome Web Store</td><td style="padding: 8px; border: 1px solid var(--border);">公开页面</td><td style="padding: 8px; border: 1px solid var(--border);">扩展机会</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">Tavily</td><td style="padding: 8px; border: 1px solid var(--border);">用户自备 API Key</td><td style="padding: 8px; border: 1px solid var(--border);">深度搜索</td></tr>
</table>
</div>

<div class="legal-section">
<h3>三、内容获取方式</h3>
<p>本产品仅通过公开 RSS 订阅和官方 API 获取数据，不使用爬虫技术绕过任何网站的访问限制或反爬措施。</p>
<p>具体技术手段包括：</p>
<ul>
<li><strong>RSS/Atom 订阅</strong>：订阅目标网站提供的公开 RSS 源，获取标题、摘要和链接</li>
<li><strong>公开 API</strong>：使用 Hacker News API、ArXiv API 等官方接口，遵守其使用条款和速率限制</li>
<li><strong>原文阅读服务</strong>：通过 Jina Reader 等合规工具提取公开可访问的网页正文</li>
</ul>
</div>

<div class="legal-section">
<h3>四、AI 转述与转化性使用</h3>
<div style="background: rgba(124,92,252,0.1); border: 1px solid rgba(124,92,252,0.3); border-radius: 8px; padding: 16px; margin: 12px 0;">
<p style="margin: 0;">🔄 <strong>本产品对原始内容进行的 AI 摘要属于「转化性使用」（Transformative Use），即在原文基础上进行了实质性转化，包括：语言翻译（英→中）、要点提炼、观点归纳、格式重组。AI 摘要不替代原文阅读，所有摘要均附有原文链接。</strong></p>
</div>
<p>转化性使用的具体表现：</p>
<ul>
<li><strong>语言转换</strong>：将英文原文翻译为中文，方便中文用户阅读</li>
<li><strong>信息提炼</strong>：从长篇文章中提取关键要点，生成简明摘要</li>
<li><strong>结构重组</strong>：将原文内容按情报分析框架重新组织</li>
<li><strong>原文溯源</strong>：每条情报均附带原文 URL，用户可一键查阅原文</li>
</ul>
</div>

<div class="legal-section">
<h3>五、原作者权益保护</h3>
<p>本产品尊重所有原始内容创作者的版权和知识产权。</p>
<ul>
<li>所有聚合内容均保留原文出处链接，引导用户访问原始网站</li>
<li>AI 摘要不进行原文的全文复制，仅提供提炼后的要点信息</li>
<li>如原文作者要求移除相关内容，我们将在收到通知后尽快处理</li>
</ul>
</div>

<div class="legal-section">
<h3>六、AI 内容标识声明</h3>
<p>根据《人工智能生成合成内容标识管理办法》（2025 年 9 月 1 日起施行），本产品对所有 AI 生成的内容做出如下标识：</p>
<ul>
<li><strong>显式标识</strong>：所有 AI 生成的摘要内容旁标注「🤖 AI 生成」文字标签，使用户可清楚识别</li>
<li><strong>模型说明</strong>：本产品支持用户自选 AI 模型（如 Gemini、OpenAI、xAI Grok 等）进行内容生成</li>
<li><strong>能力边界</strong>：AI 摘要可能会受到模型"幻觉"影响，产生事实偏差或翻译错误，不应作为唯一信息来源</li>
</ul>
</div>

<div class="legal-section">
<h3>七、侵权反馈渠道</h3>
<p>如果您认为本产品的内容侵犯了您的合法权益（包括但不限于版权、商标权等），请通过以下方式与我们联系：</p>
<ul>
<li>🔗 GitHub Issues：<a href="https://github.com/mumuer1024/Prism/issues" target="_blank">https://github.com/mumuer1024/Prism/issues</a></li>
</ul>
<p>请在通知中提供以下信息：</p>
<ul>
<li>您的身份证明（个人/机构）</li>
<li>被侵权内容的具体描述和原文链接</li>
<li>本产品中涉嫌侵权的内容描述</li>
<li>您的权利证明文件</li>
</ul>
<p>我们承诺在收到有效通知后 3 个工作日内进行初步审查，并在确认侵权后及时移除相关内容。</p>
<p style="color: var(--text-muted); font-size: 12px; margin-top: 16px;">最后更新：2026 年 3 月</p>
</div>
`
  }
};

/**
 * 打开法律声明模态框
 * @param {string} type - 声明类型: 'privacy' | 'terms' | 'sources'
 */
function openLegalModal(type) {
  const legal = LEGAL_CONTENT[type];
  if (!legal) return;

  // 创建模态框
  const modal = document.createElement('div');
  modal.id = 'legal-modal';
  modal.className = 'legal-modal';
  modal.innerHTML = `
    <div class="legal-modal-backdrop" onclick="closeLegalModal()"></div>
    <div class="legal-modal-content">
      <div class="legal-modal-header">
        <span class="legal-modal-icon">${legal.icon}</span>
        <h2 class="legal-modal-title">${legal.title}</h2>
        <button class="legal-modal-close" onclick="closeLegalModal()">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>
      <div class="legal-modal-body">
        ${legal.content}
      </div>
    </div>
  `;

  document.body.appendChild(modal);
  document.body.style.overflow = 'hidden';

  // 动画入场
  requestAnimationFrame(() => {
    modal.classList.add('show');
  });

  // ESC 关闭
  document.addEventListener('keydown', handleLegalModalEsc);
}

/**
 * 关闭法律声明模态框
 */
function closeLegalModal() {
  const modal = document.getElementById('legal-modal');
  if (modal) {
    modal.classList.remove('show');
    setTimeout(() => {
      modal.remove();
      document.body.style.overflow = '';
    }, 300);
  }
  document.removeEventListener('keydown', handleLegalModalEsc);
}

/**
 * ESC 键关闭模态框
 */
function handleLegalModalEsc(e) {
  if (e.key === 'Escape') {
    closeLegalModal();
  }
}

// 导出到全局
window.APP_VERSION = APP_VERSION;
window.openLegalModal = openLegalModal;
window.closeLegalModal = closeLegalModal;