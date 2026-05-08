import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";

export function SkeletonCard() {
    return (
        <Card className="h-full border-l-4 border-l-gray-200 dark:border-l-gray-800 shadow-sm overflow-hidden">
            <CardHeader className="pb-2">
                <div className="flex justify-between items-start gap-4">
                    <div className="space-y-2 w-full">
                        <div className="flex gap-2 mb-2">
                            <Skeleton className="h-5 w-24 rounded-full" />
                            <Skeleton className="h-5 w-20 rounded-full" />
                        </div>
                        <Skeleton className="h-7 w-3/4" />
                        <Skeleton className="h-4 w-1/2" />
                    </div>
                    <Skeleton className="h-12 w-12 rounded-full" />
                </div>
            </CardHeader>

            <CardContent className="pb-2 grid gap-4">
                <div className="flex gap-4">
                    <Skeleton className="h-16 w-1/3 rounded-lg" />
                    <div className="space-y-2 w-2/3">
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-5/6" />
                        <Skeleton className="h-4 w-4/6" />
                    </div>
                </div>

                <div className="flex justify-between items-center py-2 border-t border-b border-border/40">
                    <Skeleton className="h-10 w-1/3" />
                    <Skeleton className="h-10 w-1/3" />
                    <Skeleton className="h-10 w-1/5" />
                </div>
            </CardContent>

            <CardFooter className="pt-2 flex justify-between">
                <Skeleton className="h-4 w-32" />
                <div className="flex gap-2">
                    <Skeleton className="h-9 w-24 rounded-md" />
                    <Skeleton className="h-9 w-24 rounded-md" />
                </div>
            </CardFooter>
        </Card>
    );
}
