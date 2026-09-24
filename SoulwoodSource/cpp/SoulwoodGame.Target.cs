using UnrealBuildTool;
using System.Collections.Generic;

public class SoulwoodGameTarget : TargetRules
{
    public SoulwoodGameTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V6;
        ExtraModuleNames.Add("soulwoodgame");
    }
}
