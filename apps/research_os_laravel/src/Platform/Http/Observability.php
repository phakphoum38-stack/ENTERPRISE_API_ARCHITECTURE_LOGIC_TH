<?php
declare(strict_types=1);
namespace ResearchOS\Platform\Http;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;
final class Observability {
    public static function record(Request $request, string $event, array $attributes=[]): void {
        Log::info('research_os.platform',array_merge(['event'=>$event,'request_id'=>$request->header('X-Request-Id'),'correlation_id'=>$request->header('X-Correlation-Id'),'actor'=>$request->header('X-Actor')],$attributes));
    }
}
