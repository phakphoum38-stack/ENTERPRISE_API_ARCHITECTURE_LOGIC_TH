<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Infrastructure;

use Illuminate\Http\Client\Factory;
use Illuminate\Http\Client\PendingRequest;
use ResearchOS\Platform\Contracts\RequestContext;
use RuntimeException;

final class CanonicalPlatformClient
{
    public function __construct(private readonly Factory $http)
    {
    }

    /** @param array<string, mixed> $payload */
    public function post(RequestContext $context, string $endpoint, array $payload): array
    {
        $baseUrl = rtrim((string) config('platform.canonical.base_url', ''), '/');
        if ($baseUrl === '') {
            throw new RuntimeException('Canonical Research OS Platform URL is not configured.');
        }

        $response = $this->request($context)->post($baseUrl.$endpoint, $payload);
        $response->throw();

        $json = $response->json();
        if (!is_array($json)) {
            throw new RuntimeException('Canonical Research OS Platform returned a non-object response.');
        }

        return $json;
    }

    private function request(RequestContext $context): PendingRequest
    {
        return $this->http
            ->acceptJson()
            ->asJson()
            ->timeout((float) config('platform.canonical.timeout', 10))
            ->connectTimeout((float) config('platform.canonical.connect_timeout', 3))
            ->withHeaders([
                'X-Request-Id' => $context->requestId,
                'X-Correlation-Id' => $context->correlationId,
                'X-Contract-Version' => $context->contractVersion,
                'X-Actor' => $context->actor,
                'Idempotency-Key' => $context->requestId,
            ]);
    }
}
