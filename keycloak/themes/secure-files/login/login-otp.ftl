<#import "template.ftl" as layout>
<@layout.registrationLayout; section>
    <#if section = "form">
        <div class="form-header">
            <h2 class="form-title">Two-factor authentication</h2>
            <p class="form-subtitle">Enter the code from your authenticator app</p>
        </div>

        <form id="kc-otp-login-form" action="${url.loginAction}" method="post">
            <div class="form-group">
                <label for="otp" class="form-label">Authentication code</label>
                <input type="text" id="otp" name="otp" class="form-control" 
                       autocomplete="off" pattern="[0-9]*" inputmode="numeric"
                       autofocus />
            </div>

            <button type="submit" class="btn">
                ${msg("doSubmit")}
            </button>
        </form>

        <#if client?? && client.baseUrl?has_content>
            <div class="form-links">
                <a href="${client.baseUrl}" class="link">← Back to application</a>
            </div>
        </#if>
    </#if>
</@layout.registrationLayout>