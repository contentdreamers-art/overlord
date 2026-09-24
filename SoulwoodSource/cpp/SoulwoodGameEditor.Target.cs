using UnrealBuildTool;
using System.Collections.Generic;

public class SoulwoodGameEditorTarget : TargetRules
{
    public SoulwoodGameEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V6;
        ExtraModuleNames.Add("soulwoodgame");
    }
}
