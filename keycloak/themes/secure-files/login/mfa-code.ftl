<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=!messagesPerField.existsError('code'); section>
    <#if section = "header">
        ${msg("Enter Verification Code")}
    <#elseif section = "form">
        <div class="form-header">
            <h2 class="form-title">Verification Required</h2>
            <#if method?? && method == "totp">
                <p class="form-subtitle">Enter the code from your authenticator app</p>
            <#elseif method?? && method == "sms">
                <p class="form-subtitle">Enter the code we sent to your phone</p>
            <#elseif method?? && method == "telegram">
                <p class="form-subtitle">Enter the code we sent to your Telegram</p>
            <#else>
                <p class="form-subtitle">Enter the code we sent you</p>
            </#if>
        </div>
        
        <form id="kc-otp-login-form" class="${properties.kcFormClass!}" action="${url.loginAction}" method="post">
            <div class="verification-code-container">
                <div class="form-group">
                    <div class="verification-code-input">
                        <input id="code" name="code" type="text" 
                            autocomplete="one-time-code"
                            inputmode="numeric" 
                            pattern="[0-9]*" 
                            minlength="6" 
                            maxlength="6"
                            class="form-control"
                            autofocus required/>
                        <div class="code-hint">6-digit code</div>
                    </div>
                </div>
                
                <#if method?? && method == "totp">
                    <div class="method-info">
                        <div class="method-icon">🔐</div>
                        <p>Open your authenticator app to view the code</p>
                    </div>
                <#elseif method?? && method == "sms">
                    <div class="method-info">
                        <div class="method-icon">📱</div>
                        <p>We sent a code to your registered phone number</p>
                    </div>
                <#elseif method?? && method == "telegram">
                    <div class="method-info">
                        <div class="method-icon">✈️</div>
                        <p>We sent a code to your Telegram account</p>
                    </div>
                <#elseif method?? && method == "email">
                    <div class="method-info">
                        <div class="method-icon">📧</div>
                        <p>We sent a code to your email address</p>
                    </div>
                </#if>
            </div>

            <div class="${properties.kcFormGroupClass!}">
                <div id="kc-form-buttons" class="${properties.kcFormButtonsClass!}">
                    <input class="btn" type="submit" value="${msg('Verify')}"/>
                </div>
                
                <div class="form-options">
                    <button type="button" class="text-link" onclick="window.history.back()">
                        Use a different method
                    </button>
                </div>
            </div>
        </form>
    </#if>
</@layout.registrationLayout>