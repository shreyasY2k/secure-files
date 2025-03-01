<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=!messagesPerField.existsError('code'); section>
    <#if section = "header">
        ${msg("verifyYourEmail")}
    <#elseif section = "form">
        <div class="form-header">
            <h2 class="form-title">Verify Your Email</h2>
            <p class="form-subtitle">We've sent a verification code to your email</p>
        </div>
        
        <form id="kc-email-verify-form" class="${properties.kcFormClass!}" action="${url.loginAction}" method="post">
            <div class="verification-code-container">
                <div class="form-group">
                    <label for="code" class="form-label">
                        ${msg("emailVerificationCode")}
                    </label>
                    
                    <div class="form-info-text">
                        ${msg("emailVerificationInstruction", email!'')}
                    </div>

                    <div class="verification-code-input">
                        <input type="text" id="code" name="code" 
                            class="form-control"
                            inputmode="numeric"
                            autocomplete="one-time-code"
                            pattern="[0-9]*"
                            minlength="6"
                            maxlength="6"
                            autofocus
                            required/>
                        <div class="code-hint">6-digit code</div>
                    </div>
                </div>
                
                <div class="method-info">
                    <div class="method-icon">📧</div>
                    <p>Check your inbox for the verification code</p>
                </div>
            </div>

            <div class="${properties.kcFormGroupClass!}">
                <div id="kc-form-buttons" class="${properties.kcFormButtonsClass!}">
                    <input class="btn" type="submit" value="${msg('verify')}"/>
                </div>
            </div>
        </form>
    </#if>
</@layout.registrationLayout>