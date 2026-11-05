#ifndef BuildDir
  #define BuildDir "..\dist"
#endif
#define AppVersion "0.8.0"

[Setup]
AppId=Shanvision.Liubai.PromptLibrary
AppName={cm:AppTitle}
AppVersion={#AppVersion}
AppPublisher=Shanvision
AppPublisherURL=https://github.com/Shanvision-star/liubai-prompt-library
DefaultDirName={localappdata}\Programs\Liubai
DefaultGroupName={cm:MenuGroup}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
WizardStyle=modern
WizardBackColor=$FFFFFF
SetupIconFile=..\desktop\app.ico
UninstallDisplayIcon={app}\Liubai.exe
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=Liubai-Setup-{#AppVersion}-windows-x64
Compression=lzma2
SolidCompression=yes
CloseApplications=force
RestartApplications=no
DisableProgramGroupPage=yes
UsePreviousAppDir=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimplified"; MessagesFile: "compiler:Default.isl"

[LangOptions]
chinesesimplified.LanguageName=简体中文
chinesesimplified.LanguageID=$0804
chinesesimplified.DialogFontName=Microsoft YaHei UI

[Messages]
english.WelcomeLabel2=Liubai includes a ready-to-use prompt collection and runs without a separate Python installation.%n%nYour library is stored separately and is kept when you upgrade or uninstall.
english.FinishedLabel=[name] is ready. Open it to browse, read, and copy prompts.
english.ConfirmUninstall=Uninstall %1? The program will be removed and your library will be kept.
chinesesimplified.SetupAppTitle=安装
chinesesimplified.SetupWindowTitle=安装 - %1
chinesesimplified.UninstallAppTitle=卸载
chinesesimplified.UninstallAppFullTitle=卸载 %1
chinesesimplified.InformationTitle=信息
chinesesimplified.ConfirmTitle=确认
chinesesimplified.ErrorTitle=错误
chinesesimplified.ButtonBack=< 上一步(&B)
chinesesimplified.ButtonNext=下一步(&N) >
chinesesimplified.ButtonInstall=安装(&I)
chinesesimplified.ButtonOK=确定
chinesesimplified.ButtonCancel=取消
chinesesimplified.ButtonYes=是(&Y)
chinesesimplified.ButtonNo=否(&N)
chinesesimplified.ButtonFinish=完成(&F)
chinesesimplified.ButtonBrowse=浏览(&B)...
chinesesimplified.WelcomeLabel1=欢迎安装 [name]
chinesesimplified.WelcomeLabel2=安装后即可使用，无需另行安装 Python。%n%n内置中英文提示词、复用版本与设计拆解。个人数据单独保存在本机，升级和卸载保留数据。
chinesesimplified.WizardLicense=许可协议
chinesesimplified.LicenseLabel=请阅读使用许可。素材的来源与各自许可保留在条目中。
chinesesimplified.LicenseAccepted=我接受协议(&A)
chinesesimplified.LicenseNotAccepted=我不接受协议(&D)
chinesesimplified.WizardSelectDir=选择安装位置
chinesesimplified.SelectDirLabel3=程序将安装到以下文件夹。
chinesesimplified.SelectDirBrowseLabel=点击“下一步”继续，或“浏览”选择其他位置。
chinesesimplified.WizardSelectTasks=附加选项
chinesesimplified.SelectTasksLabel2=选择需要的附加功能，然后点击“下一步”。
chinesesimplified.WizardReady=准备安装
chinesesimplified.ReadyLabel1=即将把 [name] 安装到电脑上。
chinesesimplified.ReadyLabel2a=点击“安装”继续，或点击“上一步”修改设置。
chinesesimplified.ReadyLabel2b=点击“安装”继续。
chinesesimplified.ReadyMemoDir=安装位置：
chinesesimplified.ReadyMemoTasks=附加选项：
chinesesimplified.WizardPreparing=准备安装
chinesesimplified.WizardInstalling=正在安装
chinesesimplified.InstallingLabel=正在安装 [name]，请稍候。
chinesesimplified.FinishedHeadingLabel=安装完成
chinesesimplified.FinishedLabel=[name] 已安装。打开后即可浏览和复制内置的提示词与拆解。
chinesesimplified.FinishedLabelNoIcons=[name] 已安装。
chinesesimplified.ConfirmUninstall=要卸载 %1 吗？程序文件会被移除，个人素材目录会保留。
chinesesimplified.UninstalledAll=%1 已卸载。个人素材仍保留在原数据目录。

[CustomMessages]
english.AppTitle=Liubai · Prompt Library
english.MenuGroup=Liubai
english.OpenApp=Liubai
english.StopApp=Close Liubai
english.CreateShortcut=Create a desktop shortcut
english.LaunchApp=Open Liubai
chinesesimplified.AppTitle=留白 · 提示词素材库
chinesesimplified.MenuGroup=留白
chinesesimplified.OpenApp=留白
chinesesimplified.StopApp=关闭留白
chinesesimplified.CreateShortcut=创建桌面快捷方式
chinesesimplified.LaunchApp=打开留白

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateShortcut}"; Flags: unchecked

[Files]
Source: "{#BuildDir}\Liubai\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#BuildDir}\Liubai-MCP\*"; DestDir: "{app}\mcp"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\bundled-library\README.md"; DestDir: "{app}"; DestName: "COLLECTION.md"; Flags: ignoreversion
Source: "{#BuildDir}\runtime-licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{cm:OpenApp}"; Filename: "{app}\Liubai.exe"
Name: "{group}\{cm:StopApp}"; Filename: "{app}\Liubai.exe"; Parameters: "--stop"
Name: "{autodesktop}\{cm:OpenApp}"; Filename: "{app}\Liubai.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Liubai.exe"; Description: "{cm:LaunchApp}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\Liubai.exe"; Parameters: "--stop --no-browser"; RunOnceId: "StopLiubai"; Flags: runhidden waituntilterminated skipifdoesntexist

[Code]
procedure InitializeWizard;
begin
  WizardForm.WizardBitmapImage.Visible := False;
  WizardForm.WizardBitmapImage2.Visible := False;
  WizardForm.WizardSmallBitmapImage.Visible := False;
end;
