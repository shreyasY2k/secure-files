<#import "template.ftl" as layout>
<@layout.registrationLayout displayInfo=false; section>
    <#if section = "form">
    <div class="totp-container">
        <div class="totp-header">
            <h3>Scan the QR code below with your authenticator app</h3>
        </div>

        <div class="qr-section">
            <img src="data:image/png;base64,${totp.totpSecretQrCode}" 
                 class="qr-code" 
                 alt="QR Code for TOTP setup" />
            
            <a class="manual-setup-link" onclick="toggleManualSetup()">
                Can't scan? Click for manual setup
            </a>
            
            <div id="manual-setup" class="manual-setup">
                <p style="margin: 0 0 8px 0;">Enter this code in your app:</p>
                <code class="secret-key">${totp.totpSecret}</code>
            </div>
        </div>

        <div class="verification-section">
            <h3>Enter verification code from your app</h3>
            <form action="${url.loginAction}" method="post">
                <input type="text" 
                       id="totp" 
                       name="totp" 
                       class="totp-input"
                       autocomplete="off" 
                       pattern="[0-9]*" 
                       inputmode="numeric"
                       maxlength="6"
                       placeholder="Enter 6-digit code"
                       required />

                <input type="hidden" name="totpSecret" value="${totp.totpSecret}" />
                <input type="hidden" name="userLabel" value="" />
                <input type="hidden" name="logout-sessions" value="on" />

                <button type="submit" class="submit-button">
                    Verify and complete setup
                </button>
            </form>
        </div>
    </div>

    <script>
        function toggleManualSetup() {
            const manualSetup = document.getElementById('manual-setup');
            manualSetup.style.display = manualSetup.style.display === 'none' ? 'block' : 'none';
        }
    </script>
    </#if>
</@layout.registrationLayout>