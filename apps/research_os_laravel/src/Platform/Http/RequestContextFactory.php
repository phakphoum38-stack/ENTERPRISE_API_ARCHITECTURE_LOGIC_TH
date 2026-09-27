<?php
declare(strict_types=1);
namespace ResearchOS\Platform\Http;
use Illuminate\Http\Request;
use ResearchOS\Platform\Contracts\RequestContext;
final class RequestContextFactory {
    public function from(Request $request): RequestContext {
        $requestId = (string) ($request->header('X-Request-Id') ?: $request->header('Idempotency-Key') ?: $request->fingerprint());
        $correlationId = (string) ($request->header('X-Correlation-Id') ?: $requestId);
        $actor = (string) ($request->header('X-Actor') ?: 'unknown');
        $version = (string) ($request->header('X-Contract-Version') ?: '1.0.0');
        return new RequestContext($requestId, $correlationId, $actor, $version);
    }
}
