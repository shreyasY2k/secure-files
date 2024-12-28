<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=true; section>
    <#if section = "header">
        ${msg("registerTitle")}
    <#elseif section = "form">
        <div>
            <div class="form-header">
                <h2 class="form-title">Create an account</h2>
                <p class="form-subtitle">Join us to start sharing files securely</p>
            </div>

            <form id="kc-register-form" class="${properties.kcFormClass!}" action="${url.registrationAction}" method="post">
                <div class="name-fields">
                    <div class="form-group">
                        <label for="firstName" class="form-label">
                            ${msg("firstName")} <span class="required">*</span>
                        </label>
                        <input type="text" id="firstName" class="form-control" name="firstName"
                               value="${(register.formData.firstName!'')}"
                               aria-invalid="<#if messagesPerField.existsError('firstName')>true</#if>" />
                    </div>

                    <div class="form-group">
                        <label for="lastName" class="form-label">
                            ${msg("lastName")} <span class="required">*</span>
                        </label>
                        <input type="text" id="lastName" class="form-control" name="lastName"
                               value="${(register.formData.lastName!'')}"
                               aria-invalid="<#if messagesPerField.existsError('lastName')>true</#if>" />
                    </div>
                </div>

                <div class="form-group">
                    <label for="email" class="form-label">
                        ${msg("email")} <span class="required">*</span>
                    </label>
                    <input type="email" id="email" class="form-control" name="email"
                           value="${(register.formData.email!'')}"
                           aria-invalid="<#if messagesPerField.existsError('email')>true</#if>" /
                </div>

                <div class="form-group">
                    <label for="username" class="form-label">
                        ${msg("username")} <span class="required">*</span>
                    </label>
                    <input type="text" id="username" class="form-control" name="username"
                           value="${(register.formData.username!'')}"
                           aria-invalid="<#if messagesPerField.existsError('username')>true</#if>" /
                </div>

                <div class="form-group">
                    <label for="password" class="form-label">
                        ${msg("password")} <span class="required">*</span>
                    </label>
                    <input type="password" id="password" class="form-control" name="password"
                           aria-invalid="<#if messagesPerField.existsError('password')>true</#if>" /
                </div>

                <div class="form-group">
                    <label for="password-confirm" class="form-label">
                        ${msg("passwordConfirm")} <span class="required">*</span>
                    </label>
                    <input type="password" id="password-confirm" class="form-control" name="password-confirm"
                           aria-invalid="<#if messagesPerField.existsError('password-confirm')>true</#if>" />
                </div>

                <button class="btn" type="submit">
                    ${msg("doRegister")}
                </button>
            </form>

            <div class="register-link">
                ${msg("alreadyHaveAccount")} <a href="${url.loginUrl}">${msg("doLogIn")}</a>
            </div>
        </div>
    </#if>
</@layout.registrationLayout>