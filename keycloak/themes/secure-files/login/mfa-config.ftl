<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=!messagesPerField.existsError('mfa-config'); section>
    <#if section = "header">
        ${msg("Configure")?replace("{0}", (method!'')?capitalize)}
    <#elseif section = "form">
        <div class="form-header">
            <h2 class="form-title">Configure ${(method!'')?capitalize} Authentication</h2>
            <p class="form-subtitle">Set up your authentication details to continue</p>
        </div>
        
        <form id="kc-mfa-config-form" class="${properties.kcFormClass!}" action="${url.loginAction}" method="post">
            <input type="hidden" id="mfa-method" name="mfa-method" value="${method!''}">
            
            <div class="config-container">
                <#if method?? && method == "sms">
                    <div class="method-info">
                        <div class="method-icon">📱</div>
                        <p>We'll send verification codes to your phone number when you sign in</p>
                    </div>
                    
                    <div class="${properties.kcFormGroupClass!}">
                        <label for="phoneNumber" class="form-label">${msg("Phone Number")}</label>
                        <div class="form-input-wrapper">
                            <input type="tel" id="phoneNumber" name="phoneNumber" class="form-control"
                                   placeholder="+1234567890"
                                   value="${(phoneNumber!'')}"/>
                            <p class="input-help">Enter your full phone number with country code (e.g., +12025550123)</p>
                        </div>
                    </div>
                <#elseif method?? && method == "telegram">
                    <div class="method-info">
                        <div class="method-icon">✈️</div>
                        <p>We'll send verification codes to your Telegram account</p>
                    </div>
                    
                    <div class="${properties.kcFormGroupClass!}">
                        <label for="telegramId" class="form-label">${msg("Telegram Chat ID")}</label>
                        <div class="form-input-wrapper">
                            <input type="text" id="telegramId" name="telegramId" class="form-control"
                                   placeholder="${msg('Enter your telegram id')}"
                                   value="${(telegramId!'')}"/>
                        </div>
                        
                        <div class="telegram-instructions">
                            <h4>To get your Telegram Chat ID:</h4>
                            <ol>
                                <li>Open Telegram and search for our bot: <strong>@${msg("telegrambotusername")}</strong></li>
                                <li>Message the bot anything and it will reply with your Chat ID</li>
                                <li>Copy the Chat ID and paste it here</li>
                            </ol>
                        </div>
                    </div>
                <#elseif method?? && method == "email">
                    <div class="method-info">
                        <div class="method-icon">📧</div>
                        <p>We'll send verification codes to your email address when you sign in</p>
                    </div>
                    
                    <div class="${properties.kcFormGroupClass!}">
                        <label for="email" class="form-label">${msg("Email")}</label>
                        <div class="form-input-wrapper">
                            <input type="email" id="email" name="email" class="form-control"
                                   placeholder="${msg('Enter your email address')}"
                                   value="${(email!'')}"/>
                        </div>
                    </div>
                </#if>
            </div>

            <div class="${properties.kcFormGroupClass!}">
                <div id="kc-form-buttons" class="${properties.kcFormButtonsClass!}">
                    <input class="btn" type="submit" value="${msg('Save')}"/>
                </div>
                
                <div class="form-options">
                    <button type="button" class="text-link" onclick="window.history.back()">
                        Go back
                    </button>
                </div>
            </div>
        </form>
    </#if>
</@layout.registrationLayout>