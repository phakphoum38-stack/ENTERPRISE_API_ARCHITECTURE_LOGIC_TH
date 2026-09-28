<?php
declare(strict_types=1);
namespace ResearchOS\Platform\Application;
use ResearchOS\Platform\Contracts\RequestContext;
use ResearchOS\Platform\Contracts\ToolGateway;
final class ToolApplicationService {
    public function __construct(private readonly ToolGateway $gateway) {}
    public function invoke(RequestContext $context, string $tool, array $input): array {
        return $this->gateway->invoke($context, $tool, $input);
    }
}
