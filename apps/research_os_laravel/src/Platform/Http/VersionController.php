<?php
declare(strict_types=1);
namespace ResearchOS\Platform\Http;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use ResearchOS\Platform\Application\VersionApplicationService;
final class VersionController {
    public function __construct(private readonly VersionApplicationService $versions) {}
    public function check(Request $request): JsonResponse {
        $version=(string)$request->input('contract_version','1.0.0');
        $supported=$this->versions->supports($version);
        return response()->json(['contract_version'=>$version,'supported'=>$supported],$supported?200:409);
    }
}
