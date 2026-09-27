<?php
declare(strict_types=1);
namespace ResearchOS\Platform\Http;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use ResearchOS\Platform\Application\ControlApplicationService;
use ResearchOS\Platform\Application\OperationsApplicationService;
use ResearchOS\Platform\Application\ToolApplicationService;
final class PlatformController {
    public function __construct(
        private readonly ToolApplicationService $tools,
        private readonly ControlApplicationService $control,
        private readonly OperationsApplicationService $operations,
        private readonly RequestContextFactory $contexts,
    ) {}
    public function tool(Request $request): JsonResponse {
        $data=$request->validate(['tool'=>['required','string'],'input'=>['array']]);
        return response()->json($this->tools->invoke($this->contexts->from($request),$data['tool'],$data['input']??[]));
    }
    public function control(Request $request): JsonResponse {
        $command=$request->validate(['command'=>['required','array']])['command'];
        return response()->json($this->control->execute($this->contexts->from($request),$command));
    }
    public function operations(): JsonResponse { return response()->json($this->operations->snapshot()); }
}
