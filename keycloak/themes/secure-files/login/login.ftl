<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=true; section>
    <#if section = "form">
        <div class="form-header">
            <h2 class="form-title">Welcome back</h2>
            <p class="form-subtitle">Sign in to your account to continue</p>
        </div>

        <form id="kc-form-login" onsubmit="login.disabled = true; return true;" action="${url.loginAction}" method="post">
            <div class="form-group">
                <label for="username" class="form-label">${msg("username")}</label>
                <input tabindex="1" id="username" class="form-control" name="username" value="${(login.username!'')}" type="text" autofocus autocomplete="off" />
            </div>

            <div class="form-group">
                <label for="password" class="form-label">${msg("password")}</label>
                <input tabindex="2" id="password" class="form-control" name="password" type="password" autocomplete="off" />
            </div>

                <#if realm.resetPasswordAllowed>
                    <a tabindex="5" class="link" href="${url.loginResetCredentialsUrl}">${msg("doForgotPassword")}</a>
                </#if>
            
            <button tabindex="4" class="btn" type="submit">
                ${msg("doLogIn")}
            </button>
        </form>

        <#if realm.password && realm.registrationAllowed && !registrationDisabled??>
            <div class="register-link">
                ${msg("noAccount")} <a tabindex="6" href="${url.registrationUrl}">${msg("doRegister")}</a>
            </div>
        </#if>
    </#if>
</@layout.registrationLayout>