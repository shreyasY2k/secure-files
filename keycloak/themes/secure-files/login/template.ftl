<#macro registrationLayout bodyClass="" displayInfo=false displayMessage=true displayRequiredFields=false showAnotherWayIfPresent=true>
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${msg("loginTitle", (realm.displayName!''))}</title>
    <link href="${url.resourcesPath}/css/styles.css" rel="stylesheet" />
</head>
<body>
    <div class="flex min-h-screen">
        <!-- Left Column - Brand/Features -->
        <div class="brand-section">
            <div class="brand-content">
                <div class="brand-logo">
                    <svg viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 2L2 7L12 12L22 7L12 2Z" />
                        <path d="M2 17L12 22L22 17" />
                        <path d="M2 12L12 17L22 12" />
                    </svg>
                </div>
                
                <h1 class="brand-title">Secure File Sharing Platform</h1>
                <p class="brand-description">Share your files securely with end-to-end encryption and advanced access controls.</p>

                <div class="features">
                    <div class="feature-item">
                        <div class="feature-icon">🔒</div>
                        <div class="feature-text">
                            <h3>End-to-End Encryption</h3>
                            <p>Your files are encrypted before upload and remain secure throughout transmission.</p>
                        </div>
                    </div>

                    <div class="feature-item">
                        <div class="feature-icon">🔑</div>
                        <div class="feature-text">
                            <h3>Access Control</h3>
                            <p>Set permissions, expiration dates, and access limits for shared files.</p>
                        </div>
                    </div>

                    <div class="feature-item">
                        <div class="feature-icon">⚡</div>
                        <div class="feature-text">
                            <h3>Fast & Reliable</h3>
                            <p>Quick uploads and downloads with reliable storage and performance.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Right Column - Form Content -->
        <div class="form-section">
            <div class="form-container">
                <#if displayMessage && message?has_content>
                    <div class="alert alert-${message.type}">
                        ${kcSanitize(message.summary)?no_esc}
                    </div>
                </#if>

                <#nested "form">

                <#if displayInfo>
                    <div class="info-text">
                        <#nested "info">
                    </div>
                </#if>
            </div>
        </div>
    </div>
</body>
</html>
</#macro>
