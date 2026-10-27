#ifndef BuildDir
  #define BuildDir "..\dist"
#endif
#define AppVersion "0.6.0"

[Setup]
AppId=Shanvision.Liubai.PromptLibrary
AppName=留白 · 提示词素材库
AppVersion={#AppVersion}
AppPublisher=Shanvision
AppPublisherURL=https://github.com/Shanvision-star/liubai-prompt-library
DefaultDirName={localappdata}\Programs\Liubai
DefaultGroupName=留白
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
Name: "chinesesimplified"; MessagesFile: "compiler:Default.isl"

[LangOptions]
LanguageName=简体中文
LanguageID=$0804
DialogFontName=Microsoft YaHei UI

[Messages]
SetupAppTitle=安装
SetupWindowTitle=安装 - %1
UninstallAppTitle=卸载
UninstallAppFullTitle=卸载 %1
InformationTitle=信息
ConfirmTitle=确认
ErrorTitle=错误
ButtonBack=< 上一步(&B)
ButtonNext=下一步(&N) >
ButtonInstall=安装(&I)
ButtonOK=确定
ButtonCancel=取消
ButtonYes=是(&Y)
ButtonNo=否(&N)
ButtonFinish=完成(&F)
ButtonBrowse=浏览(&B)...
WelcomeLabel1=欢迎安装 [name]
WelcomeLabel2=安装后即可使用，无需另行安装 Python。%n%n内置汉化提示词、中文复用版本与设计拆解。个人数据单独保存在本机，升级和卸载保留数据。
WizardLicense=许可协议
LicenseLabel=请阅读使用许可。素材的来源与各自许可保留在条目中。
LicenseAccepted=我接受协议(&A)
LicenseNotAccepted=我不接受协议(&D)
WizardSelectDir=选择安装位置
SelectDirLabel3=程序将安装到以下文件夹。
SelectDirBrowseLabel=点击“下一步”继续，或“浏览”选择其他位置。
WizardSelectTasks=附加选项
SelectTasksLabel2=选择需要的附加功能，然后点击“下一步”。
WizardReady=准备安装
ReadyLabel1=即将把 [name] 安装到电脑上。
ReadyLabel2a=点击“安装”继续，或点击“上一步”修改设置。
ReadyLabel2b=点击“安装”继续。
ReadyMemoDir=安装位置：
ReadyMemoTasks=附加选项：
WizardPreparing=准备安装
WizardInstalling=正在安装
InstallingLabel=正在安装 [name]，请稍候。
FinishedHeadingLabel=安装完成
FinishedLabel=[name] 已安装。打开后即可浏览和复制内置的汉化提示词与拆解。
FinishedLabelNoIcons=[name] 已安装。
ConfirmUninstall=要卸载 %1 吗？程序文件会被移除，个人素材目录会保留。
UninstalledAll=%1 已卸载。个人素材仍保留在原数据目录。

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; Flags: unchecked

[Files]
Source: "{#BuildDir}\Liubai\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#BuildDir}\Liubai-MCP\*"; DestDir: "{app}\mcp"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\bundled-library\README.md"; DestDir: "{app}"; DestName: "COLLECTION.md"; Flags: ignoreversion
Source: "{#BuildDir}\runtime-licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\留白"; Filename: "{app}\Liubai.exe"
Name: "{group}\关闭留白"; Filename: "{app}\Liubai.exe"; Parameters: "--stop"
Name: "{autodesktop}\留白"; Filename: "{app}\Liubai.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Liubai.exe"; Description: "打开留白"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\Liubai.exe"; Parameters: "--stop --no-browser"; RunOnceId: "StopLiubai"; Flags: runhidden waituntilterminated skipifdoesntexist

[Code]
procedure InitializeWizard;
begin
  WizardForm.WizardBitmapImage.Visible := False;
  WizardForm.WizardBitmapImage2.Visible := False;
  WizardForm.WizardSmallBitmapImage.Visible := False;
end;
