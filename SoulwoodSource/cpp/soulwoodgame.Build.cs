using UnrealBuildTool;

public class soulwoodgame : ModuleRules
{
    public soulwoodgame(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new string[] {
            "Core", "CoreUObject", "Engine", "InputCore", "UMG"
        });
    }
}
