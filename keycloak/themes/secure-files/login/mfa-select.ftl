<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=!messagesPerField.existsError('mfa-method'); section>
    <#if section = "header">
        ${msg("Select 2FA Method")}
    <#elseif section = "form">
        <div class="form-header">
            <h2 class="form-title">Select Authentication Method</h2>
            <p class="form-subtitle">Choose your preferred second factor authentication method</p>
        </div>
        
        <form id="kc-select-mfa-form" class="${properties.kcFormClass!}" action="${url.loginAction}" method="post">
            <div class="mfa-methods-grid">
                <#-- Email Method -->
                <div class="mfa-method-card ${(email_configured?? && email_configured)?string('configured', 'not-configured')}">
                    <div class="mfa-method-radio">
                        <input type="radio" id="email" name="mfa-method" value="email" 
                            <#if email_configured?? && email_configured>checked</#if>>
                        <label for="email" class="mfa-method-label">
                            <div class="mfa-method-icon">
                                <span class="icon">📧</span>
                            </div>
                            <div class="mfa-method-info">
                                <span class="mfa-method-name">Email</span>
                                <#if !email_configured?? || !email_configured>
                                    <span class="mfa-method-status">${msg("Not Configured")}</span>
                                <#else>
                                    <span class="mfa-method-status">Ready</span>
                                </#if>
                            </div>
                        </label>
                    </div>
                </div>

                <#-- SMS Method -->
                <div class="mfa-method-card ${(sms_configured?? && sms_configured)?string('configured', 'not-configured')}">
                    <div class="mfa-method-radio">
                        <input type="radio" id="sms" name="mfa-method" value="sms" 
                            <#if sms_configured?? && sms_configured>checked</#if>>
                        <label for="sms" class="mfa-method-label">
                            <div class="mfa-method-icon">
                                <span class="icon">📱</span>
                            </div>
                            <div class="mfa-method-info">
                                <span class="mfa-method-name">SMS</span>
                                <#if !sms_configured?? || !sms_configured>
                                    <span class="mfa-method-status">${msg("Not Configured")}</span>
                                <#else>
                                    <span class="mfa-method-status">Ready</span>
                                </#if>
                            </div>
                        </label>
                    </div>
                </div>

                <#-- Telegram Method -->
                <div class="mfa-method-card ${(telegram_configured?? && telegram_configured)?string('configured', 'not-configured')}">
                    <div class="mfa-method-radio">
                        <input type="radio" id="telegram" name="mfa-method" value="telegram" 
                            <#if telegram_configured?? && telegram_configured>checked</#if>>
                        <label for="telegram" class="mfa-method-label">
                            <div class="mfa-method-icon">
                                <span class="icon">✈️</span>
                            </div>
                            <div class="mfa-method-info">
                                <span class="mfa-method-name">Telegram</span>
                                <#if !telegram_configured?? || !telegram_configured>
                                    <span class="mfa-method-status">${msg("Not Configured")}</span>
                                <#else>
                                    <span class="mfa-method-status">Ready</span>
                                </#if>
                            </div>
                        </label>
                    </div>
                </div>

                <#-- TOTP Method -->
                <div class="mfa-method-card ${(totp_configured?? && totp_configured)?string('configured', 'not-configured')}">
                    <div class="mfa-method-radio">
                        <input type="radio" id="totp" name="mfa-method" value="totp" 
                            <#if totp_configured?? && totp_configured>checked</#if>>
                        <label for="totp" class="mfa-method-label">
                            <div class="mfa-method-icon">
                                <span class="icon">🔐</span>
                            </div>
                            <div class="mfa-method-info">
                                <span class="mfa-method-name">Authenticator App</span>
                                <#if !totp_configured?? || !totp_configured>
                                    <span class="mfa-method-status">${msg("Not Configured")}</span>
                                <#else>
                                    <span class="mfa-method-status">Ready</span>
                                </#if>
                            </div>
                        </label>
                    </div>
                </div>
            </div>

            <div class="${properties.kcFormGroupClass!}">
                <div id="kc-form-buttons" class="${properties.kcFormButtonsClass!}">
                    <input class="btn" type="submit" value="${msg('Continue')}"/>
                </div>
            </div>
        </form>
    </#if>
</@layout.registrationLayout>