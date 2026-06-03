/**
 * Legal Module - 隐私政策、用户协议、数据来源声明
 * 法务模块 - 法律声明和条款
 */

// 应用版本号
const APP_VERSION = 'v2.1.0';

// 法律声明内容
const LEGAL_CONTENT = {
  privacy: {
    title: '隐私政策',
    icon: '🔒',
    content: `
<div class="legal-section">
<h3>一、引言</h3>
<p>「Prism - 棱镜情报」（以下简称"本产品"）是一款 AI 驱动的开源情报聚合工具，由独立开发者运营。<strong>本产品仅提供工具使用权，所有 AI 功能均由用户自备 API Key 直连调用，我们不代理、不持久存储、不触碰您的 API 密钥和 AI 请求内容。</strong></p>
<p>我们深知个人信息保护的重要性，并严格遵守《中华人民共和国个人信息保护法》（PIPL）、《数据安全法》及《网络安全法》等相关法律法规。本政策旨在向您说明我们如何收集、使用和保护信息。</p>
</div>

<div class="legal-section">
<h3>二、服务模式与信息收集</h3>

<h4>2.1 免费试用（无需激活）</h4>
<p>使用免费试用服务时，<strong>我们不要求您提供任何个人信息</strong>，也不收集姓名、手机号、邮箱等个人身份信息。</p>
<p>我们仅在您的浏览器本地存储中写入以下技术标识符：</p>
<ul>
<li><strong>访客标识（visitor_id）</strong>：由您的浏览器本地生成的随机 UUID，用于统计每日免费使用次数，不含任何个人隐私数据，仅存储在您的设备本地。</li>
<li><strong>设备标识（device_id）</strong>：同上，由浏览器本地生成，用于激活码设备绑定管理。</li>
</ul>

<h4>2.2 激活码服务</h4>
<p>使用激活码激活本产品时，我们在服务器端存储以下信息：</p>
<ul>
<li><strong>激活码状态</strong>：激活码是否已激活、剩余使用次数、激活时间</li>
<li><strong>设备标识</strong>：绑定的设备 ID（由您的浏览器本地生成的随机字符串，不含任何个人身份信息）。用户主动清除浏览器本地数据后，原设备标识将失效，系统视为新设备并占用新的绑定名额。</li>
<li><strong>推荐关系</strong>：如您激活时填写了推荐码，我们记录推荐码关联关系，用于发放推荐奖励。推荐关系仅关联激活码字符串，不关联任何用户身份信息。每个激活码仅能享受一次被推荐奖励。</li>
</ul>
<p>我们<strong>不收集</strong>您的真实姓名、邮箱、手机号、身份证号等任何个人身份信息。</p>

<h4>2.3 我们不收集的信息</h4>
<ul>
<li>❌ 不收集真实姓名、身份证号、手机号、邮箱</li>
<li>❌ 不收集银行卡等支付信息（支付由第三方平台处理）</li>
<li>❌ <strong>不持久存储您的 API Key</strong>（存储在您的浏览器本地）</li>
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
<li><strong>存储位置</strong>：您的浏览器本地存储（localStorage）</li>
<li><strong>传输方式</strong>：仅在您触发任务时，由您的浏览器读取并通过加密通道传输至本产品服务端，服务端用于调用 AI 服务后立即丢弃，不做任何持久化存储</li>
<li><strong>我们的角色</strong>：我们不持久存储您的 API Key，不将其用于任何其他目的</li>
</ul>

<h4>3.2 AI 请求流向</h4>
<pre style="background: var(--bg-tertiary); padding: 12px; border-radius: 8px; font-size: 13px; color: var(--text);">
您的浏览器（读取本地 API Key）
    ↓ HTTPS 加密传输
本产品服务端（转发请求，不持久存储 Key）
    ↓
您选择的 AI 服务商
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
<tr><td style="padding: 8px; border: 1px solid var(--border);">用户 API Key</td><td style="padding: 8px; border: 1px solid var(--border);">浏览器本地</td><td style="padding: 8px; border: 1px solid var(--border);">不持久存储于服务器</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">数据源配置</td><td style="padding: 8px; border: 1px solid var(--border);">浏览器本地</td><td style="padding: 8px; border: 1px solid var(--border);">不上传服务器</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">Prompt 模板</td><td style="padding: 8px; border: 1px solid var(--border);">服务器（按激活码隔离）</td><td style="padding: 8px; border: 1px solid var(--border);">用于多设备同步</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">生成的报告</td><td style="padding: 8px; border: 1px solid var(--border);">服务器（按激活码隔离）</td><td style="padding: 8px; border: 1px solid var(--border);">30 天自动清理</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">访客标识</td><td style="padding: 8px; border: 1px solid var(--border);">浏览器本地</td><td style="padding: 8px; border: 1px solid var(--border);">不上传服务器</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">激活码状态</td><td style="padding: 8px; border: 1px solid var(--border);">服务器</td><td style="padding: 8px; border: 1px solid var(--border);">激活码存续期间保留</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">设备绑定记录</td><td style="padding: 8px; border: 1px solid var(--border);">服务器</td><td style="padding: 8px; border: 1px solid var(--border);">激活码存续期间保留</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">推荐关系记录</td><td style="padding: 8px; border: 1px solid var(--border);">服务器</td><td style="padding: 8px; border: 1px solid var(--border);">激活码存续期间保留，仅含激活码字符串</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">审计日志</td><td style="padding: 8px; border: 1px solid var(--border);">服务器</td><td style="padding: 8px; border: 1px solid var(--border);">滚动保留最近 180 天</td></tr>
</table>

<h4>4.2 关于审计日志</h4>
<p>审计日志仅记录管理员在后台执行的操作行为，包括：操作类型、操作时间、管理员标识、被操作对象 ID 及操作详情。<strong>不记录普通用户的使用行为、Prompt 内容或 API Key 信息。</strong>管理员 IP 地址会被记录用于安全审查，属于技术元数据，不用于识别任何普通用户身份。审计日志滚动保留最近 180 天，符合《网络安全法》关于日志留存不少于 6 个月的要求。</p>

<h4>4.3 数据保留期限</h4>
<table style="width: 100%; border-collapse: collapse; font-size: 13px;">
<tr><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">数据类型</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">保留期限</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">说明</th></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">激活码状态</td><td style="padding: 8px; border: 1px solid var(--border);">激活码存续期间</td><td style="padding: 8px; border: 1px solid var(--border);">次数耗尽后可申请清除</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">设备绑定记录</td><td style="padding: 8px; border: 1px solid var(--border);">激活码存续期间</td><td style="padding: 8px; border: 1px solid var(--border);">可随时解绑设备</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">云端保存的报告</td><td style="padding: 8px; border: 1px solid var(--border);">30 天</td><td style="padding: 8px; border: 1px solid var(--border);">自动清理过期报告</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">推荐关系记录</td><td style="padding: 8px; border: 1px solid var(--border);">激活码存续期间</td><td style="padding: 8px; border: 1px solid var(--border);">用于奖励发放</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">审计日志</td><td style="padding: 8px; border: 1px solid var(--border);">180 天（滚动保留）</td><td style="padding: 8px; border: 1px solid var(--border);">符合《网络安全法》要求</td></tr>
</table>

<h4>4.4 私有化配置服务</h4>
<p>如您购买私有化配置服务，所有数据存储在您自己的服务器，由您自行管理和保护。</p>
</div>

<div class="legal-section">
<h3>五、第三方服务</h3>
<p>本产品使用以下第三方服务，请注意其独立的隐私政策：</p>
<table style="width: 100%; border-collapse: collapse; font-size: 13px;">
<tr><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">服务商</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">用途</th></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">OpenAI / Google Gemini / xAI Grok / 其他</td><td style="padding: 8px; border: 1px solid var(--border);">AI 内容生成（用户自选，经服务端转发，Key 不持久存储）</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">数据源（Hacker News、36Kr 等）</td><td style="padding: 8px; border: 1px solid var(--border);">资讯聚合</td></tr>
</table>
</div>

<div class="legal-section">
<h3>六、AI 生成内容声明</h3>
<div style="background: rgba(124,92,252,0.1); border: 1px solid rgba(124,92,252,0.3); border-radius: 8px; padding: 16px; margin: 12px 0;">
<p style="margin: 0;">🤖 <strong>本产品使用 AI 技术对公开资讯进行摘要、翻译和分析。所有 AI 生成的内容均强制显示「AI 生成」标识，本产品不提供关闭此标识的选项，以确保信息透明度和用户知情权，符合《人工智能生成合成内容标识管理办法》（2025 年 9 月 1 日起施行）的要求。</strong></p>
</div>
<p>AI 生成内容可能存在"幻觉"、不准确或过时的情况，仅供参考，不代表原文观点，不构成任何投资、法律或专业决策建议。用户应自行核实信息的准确性，并对基于本产品内容所做的任何决策承担全部责任。</p>
</div>

<div class="legal-section">
<h3>七、用户权利</h3>
<p>根据相关法律法规，您享有以下权利：</p>
<ul>
<li><strong>知情权</strong>：通过本政策了解信息处理规则</li>
<li><strong>访问权</strong>：可随时查看您的激活码状态和设备绑定情况</li>
<li><strong>删除权</strong>：可申请删除您的激活码相关数据</li>
<li><strong>设备管理权</strong>：可随时解绑已绑定的设备</li>
<li><strong>数据可携带权</strong>：可导出您的配置和报告数据</li>
</ul>
<p>如需行使上述权利，请通过本政策底部的联系方式与我们联系。</p>
</div>

<div class="legal-section">
<h3>八、未成年人保护</h3>
<p>本产品不面向未满 14 周岁的未成年人。由于本产品不收集任何可识别用户身份的个人信息，我们无法主动识别用户年龄。如监护人发现未成年人使用本产品，建议立即停止使用。</p>
</div>

<div class="legal-section">
<h3>九、安全措施</h3>
<ul>
<li>全链路 HTTPS 加密传输</li>
<li>API Key 仅在请求转发时使用，不做持久化存储</li>
<li>设备标识由用户浏览器本地生成，不含个人信息</li>
<li>审计日志不记录任何普通用户可识别身份的信息</li>
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
<p style="color: var(--text-muted); font-size: 12px; margin-top: 16px;">最后更新：2026 年 4 月</p>
</div>
`
  },

  terms: {
    title: '用户服务协议',
    icon: '📋',
    content: `
<div class="legal-section">
<h3>一、服务范围</h3>
<p>「Prism - 棱镜情报」（以下简称"本产品"）是一款面向技术从业者、内容创作者和信息爱好者的 AI 情报聚合工具。本产品提供以下核心服务：</p>
<ul>
<li>聚合公开渠道（RSS 订阅、公开 API）的科技、AI、经济等领域资讯</li>
<li>使用 AI 技术对原文进行摘要提炼和中文翻译（需用户自备 API Key）</li>
<li>提供可定制的数据源配置和 Prompt 模板</li>
<li>本产品仅为本地运行的辅助工具，用户需自行承担网络环境及数据源访问的合法性责任</li>
</ul>
</div>

<div class="legal-section">
<h3>二、AI 生成内容免责声明</h3>
<div style="background: rgba(255,107,107,0.1); border: 1px solid rgba(255,107,107,0.3); border-radius: 8px; padding: 16px; margin: 12px 0;">
<p style="margin: 0;">⚠️ <strong>本产品中标注「AI 生成」的内容由大语言模型自动生成。</strong></p>
</div>
<ul>
<li>AI 生成内容可能存在"幻觉"、不准确或过时的情况</li>
<li>AI 生成内容不构成投资建议、法律意见或任何专业决策建议</li>
<li>用户应自行核实信息的准确性，并对基于本产品内容所做的任何决策承担全部责任</li>
</ul>
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
<li>将您的激活码恶意分享给他人用于商业牟利或规避使用限制</li>
</ul>
</div>

<div class="legal-section">
<h3>五、激活码服务条款</h3>

<h4>5.1 激活码说明</h4>
<p>本产品采用激活码（软件使用权授权）模式提供付费服务：</p>
<ul>
<li>激活码购买后<strong>无有效期限制</strong>，以使用次数为计量单位</li>
<li>每个激活码最多绑定 <strong>3 个设备</strong>（浏览器）</li>
<li>次数用完后可另行购买激活码叠加使用</li>
<li>激活码通过闲鱼或官方指定渠道购买，购买后由开发者人工发放</li>
</ul>

<h4>5.2 设备绑定</h4>
<ul>
<li>激活时系统将绑定您当前使用的设备标识</li>
<li>超出设备上限时，需先解绑已有设备方可在新设备上使用</li>
<li>浏览器清除本地存储数据后，原设备标识将失效，系统视为新设备并占用新的绑定名额</li>
<li>因用户主动清除浏览器数据导致的设备绑定失效，开发者不承担责任</li>
</ul>

<h4>5.3 推荐奖励</h4>
<ul>
<li>推荐他人购买并激活本产品可获得额外使用次数奖励</li>
<li>推荐奖励在被推荐人<strong>首次消费</strong>（使用次数扣减）时触发</li>
<li>推荐人每成功推荐一人获得 <strong>3 次奖励</strong>，无上限</li>
<li>每个激活码仅能享受一次被推荐奖励，被推荐人获得 3 次奖励</li>
<li>开发者保留调整推荐奖励规则的权利，调整前会提前公告</li>
</ul>

<h4>5.4 退款政策</h4>
<ul>
<li>激活码<strong>一经激活，不支持退款</strong></li>
<li>未激活的激活码可在购买后 7 日内联系开发者申请退款</li>
<li>因用户自身原因（如激活码遗失、设备超限等）导致的损失，开发者不承担退款责任</li>
</ul>
</div>

<div class="legal-section">
<h3>六、服务可用性与额度限制</h3>
<p>本产品作为独立极客项目，以"现状"（as-is）提供服务。以下情况可能导致服务中断或功能限制：</p>
<ul>
<li>激活码次数耗尽</li>
<li>短时间内发起的超高频异常请求</li>
<li>第三方服务（AI 模型服务商）的不可抗力中断</li>
<li>数据源（RSS 订阅等）的反爬拦截或结构变更</li>
</ul>
<p>对于正常的服务中断，我们不承担赔偿责任，但会以最高优先级抢修。</p>
</div>

<div class="legal-section">
<h3>七、API Key 安全责任</h3>
<p>本产品的 AI 功能需要您自备 API Key，您需自行承担以下责任：</p>
<ul>
<li>妥善保管您的 API Key，不得泄露给他人</li>
<li>定期检查 API Key 的使用情况，发现异常及时更换</li>
<li>因 API Key 泄露导致的损失由您自行承担</li>
<li>遵守您所使用的 AI 服务商的服务条款</li>
</ul>
<p>本产品开发者<strong>不持有、不访问、不持久存储</strong>用户的 API Key。API Key 的申请、充值、合规性均由用户自行负责。开发者不对因 API Key 被封禁或欠费导致的服务中断负责。</p>
</div>

<div class="legal-section">
<h3>八、私有化配置服务</h3>
<p>如您购买私有化配置服务（自行部署版本的技术咨询支持），服务范围和费用以双方协商为准。私有化部署后的所有数据由您自行管理和保护，开发者不承担相关数据安全责任。</p>
</div>

<div class="legal-section">
<h3>九、免责声明</h3>
<ul>
<li>本产品不对 AI 生成内容的准确性、完整性或时效性做出任何明示或暗示的保证</li>
<li>用户基于本产品内容做出的任何投资、商业或个人决策，由用户自行承担风险与后果</li>
<li>对于因第三方服务（AI 服务商、数据源等）故障导致的服务中断，我们不承担责任</li>
<li>用户因未妥善保管 API Key 导致的损失，我们不承担责任</li>
<li>用户因清除浏览器本地数据导致的激活码绑定失效，我们不承担责任</li>
</ul>
</div>

<div class="legal-section">
<h3>十、协议变更</h3>
<p>我们保留随时修改本协议的权利。修改后的协议将在本页面更新并注明最新日期。继续使用本产品即视为接受修改后的协议。重大变更将通过产品内通知方式告知。</p>
</div>

<div class="legal-section">
<h3>十一、适用法律与争议解决</h3>
<p>本协议的订立、履行、解释及争议解决均适用中华人民共和国法律（不包括港澳台地区法律）。因本协议引发的任何争议，双方应首先友好协商解决；协商不成的，任何一方均可向本产品开发者所在地有管辖权的人民法院提起诉讼。</p>
<p style="color: var(--text-muted); font-size: 12px; margin-top: 16px;">最后更新：2026 年 4 月</p>
</div>
`
  },

  sources: {
    title: '数据来源声明',
    icon: '📡',
    content: `
<div class="legal-section">
<h3>一、数据来源概述</h3>
<p>「Prism - 棱镜情报」聚合来自以下公开渠道的信息，所有数据均来自各平台的公开前端接口或官方 API。</p>
</div>

<div class="legal-section">
<h3>二、数据源详情</h3>

<h4>2.1 科技前沿与开源趋势</h4>
<table style="width: 100%; border-collapse: collapse; font-size: 13px;">
<tr><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">数据源</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">获取方式</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">内容类型</th></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">Hacker News</td><td style="padding: 8px; border: 1px solid var(--border);">官方公开 API</td><td style="padding: 8px; border: 1px solid var(--border);">技术热点讨论</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">HN Hiring</td><td style="padding: 8px; border: 1px solid var(--border);">官方公开 API</td><td style="padding: 8px; border: 1px solid var(--border);">技术岗位招聘信息</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">GitHub Trending</td><td style="padding: 8px; border: 1px solid var(--border);">公开页面</td><td style="padding: 8px; border: 1px solid var(--border);">开源项目趋势</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">ArXiv</td><td style="padding: 8px; border: 1px solid var(--border);">官方 API</td><td style="padding: 8px; border: 1px solid var(--border);">学术论文</td></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">HN Top Blogs</td><td style="padding: 8px; border: 1px solid var(--border);">RSS 订阅</td><td style="padding: 8px; border: 1px solid var(--border);">技术博客</td></tr>
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
<tr><td style="padding: 8px; border: 1px solid var(--border);">V2EX</td><td style="padding: 8px; border: 1px solid var(--border);">公开 RSS</td><td style="padding: 8px; border: 1px solid var(--border);">社区热议与需求</td></tr>
</table>

<h4>2.4 热榜聚合（DailyHotApi）</h4>
<table style="width: 100%; border-collapse: collapse; font-size: 13px;">
<tr><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">数据源</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">获取方式</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">内容类型</th></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">微博热搜、知乎热榜等</td><td style="padding: 8px; border: 1px solid var(--border);">DailyHotApi（开源项目）</td><td style="padding: 8px; border: 1px solid var(--border);">国内平台热榜</td></tr>
</table>
<p>DailyHotApi 为开源项目，通过各平台公开接口聚合热榜数据，项目地址：<a href="https://github.com/imsyy/DailyHotApi" target="_blank">https://github.com/imsyy/DailyHotApi</a></p>
<p style="color: var(--text-muted); font-size: 12px;">免责说明：对于 DailyHotApi 项目因获取国内平台热榜数据而可能引发的任何法律争议，本产品开发者不承担连带责任。建议用户仅将此类数据用于个人研究目的。</p>

<h4>2.5 社交与情绪（用户自备）</h4>
<table style="width: 100%; border-collapse: collapse; font-size: 13px;">
<tr><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">数据源</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">获取方式</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">内容类型</th></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">X (Twitter)</td><td style="padding: 8px; border: 1px solid var(--border);">用户自备 xAI API Key</td><td style="padding: 8px; border: 1px solid var(--border);">行业动态与社交情绪</td></tr>
</table>

<h4>2.6 深度搜索（用户自备）</h4>
<table style="width: 100%; border-collapse: collapse; font-size: 13px;">
<tr><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">数据源</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">获取方式</th><th style="text-align: left; padding: 8px; border: 1px solid var(--border);">内容类型</th></tr>
<tr><td style="padding: 8px; border: 1px solid var(--border);">Tavily</td><td style="padding: 8px; border: 1px solid var(--border);">用户自备 API Key</td><td style="padding: 8px; border: 1px solid var(--border);">深度网络搜索</td></tr>
</table>
</div>

<div class="legal-section">
<h3>三、内容获取方式</h3>
<p>本产品仅通过公开 RSS 订阅和官方 API 获取数据，不使用爬虫技术绕过任何网站的访问限制或反爬措施。</p>
<p>具体技术手段包括：</p>
<ul>
<li><strong>RSS/Atom 订阅</strong>：订阅目标网站提供的公开 RSS 源，获取标题、摘要和链接</li>
<li><strong>公开 API</strong>：使用 Hacker News API、ArXiv API、Product Hunt API 等官方接口，遵守其使用条款和速率限制</li>
<li><strong>DailyHotApi</strong>：通过自托管的开源热榜聚合服务获取国内平台公开热榜数据</li>
<li><strong>用户自备 Key</strong>：X (Twitter) 搜索和 Tavily 深度搜索由用户自行提供 API Key，本产品不存储相关 Key</li>
<li>严格遵守各数据源的 robots.txt 协议及使用条款，不干扰网站正常运行</li>
<li>我们将定期审查各数据源的使用条款变更，如发现合规风险将及时调整或移除相关数据源</li>
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
<li>严格遵守各数据源的 robots.txt 协议及使用条款，不干扰网站正常运行</li>
<li>如原文作者要求移除相关内容，我们将在收到通知后 3 个工作日内处理</li>
</ul>
</div>

<div class="legal-section">
<h3>六、AI 内容标识声明</h3>
<p>根据《人工智能生成合成内容标识管理办法》（2025 年 9 月 1 日起施行），本产品对所有 AI 生成的内容做出如下标识：</p>
<ul>
<li><strong>强制显示</strong>：所有 AI 生成的摘要内容旁强制标注「🤖 AI 生成」文字标签，不提供关闭选项</li>
<li><strong>模型说明</strong>：本产品支持用户自选 AI 模型（如 Gemini、OpenAI、xAI Grok 等）进行内容生成</li>
<li><strong>能力边界</strong>：AI 摘要可能受模型"幻觉"影响，产生事实偏差或翻译错误，不应作为唯一信息来源</li>
</ul>
</div>

<div class="legal-section">
<h3>七、侵权反馈渠道</h3>
<p>如果您认为本产品的内容侵犯了您的合法权益（包括但不限于版权、商标权等），请通过以下方式联系：</p>
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
<p style="color: var(--text-muted); font-size: 12px; margin-top: 16px;">最后更新：2026 年 4 月</p>
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